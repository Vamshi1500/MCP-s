from mcp.server.fastmcp import FastMCP
from typing import Annotated
import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from docx import Document
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.document_loaders import TextLoader
from qdrant_client.models import PointStruct, VectorParams
from transformers import AutoTokenizer, AutoModel
import torch
import uuid

# Load environment variables from .env file
load_dotenv()

API_VERSION = os.getenv("apiVersion")
API_KEY = os.getenv("apiKey")
API_BASE = os.getenv("apiBase")
MODEL_NAME = os.getenv("modelName")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2" 

# Create an MCP instance
mcp = FastMCP("Qdrant_Connection_MCP")

tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)

def encode_text(text: str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    # Use the mean of the last hidden state as the embedding
    embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return embeddings

def generate_unique_id():
    return str(uuid.uuid4())

@mcp.tool()
def create_qdrant_collection(
    collection_name: Annotated[str, "Name of the Qdrant collection to create"],
    vector_size: Annotated[int, "Dimension of the vector embeddings"]
) -> str:
    """Create a new collection in Qdrant with the specified name, vector size, and configuration."""

    try:
        # Initialize Qdrant Client
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )

        # Check if the collection already exists
        collections = client.get_collections().collections
        if collection_name in [c.name for c in collections]:
            return f"Collection '{collection_name}' already exists."

        # Create the new collection with vectors_config
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "default": VectorParams(
                    size=vector_size,
                    distance="Cosine"  # You can change this to 'Euclidean' or 'Dot' if needed
                )
            }
        )

        return f"Collection '{collection_name}' created successfully with vector size {vector_size}."

    except Exception as e:
        return f"Failed to create collection '{collection_name}': {e}"
    
# Tool to connect to Qdrant and check collection
@mcp.tool()
def connect_to_qdrant() -> str:
    """Connect to Qdrant Cloud and list available collections."""
    try:
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        response = client.get_collections()
        collections = [c.name for c in response.collections]

        if not collections:
            return "Connected to Qdrant successfully, but no collections found."
        return f"Connected to Qdrant. Available collections: {collections}"

    except Exception as e:
        return f"Failed to connect to Qdrant: {e}"

@mcp.tool()
def ingest_doc_to_qdrant(
    file_path: Annotated[str, "Path to the document (PDF, DOCX, or TXT)"],
    collection_name: Annotated[str, "Name of the Qdrant collection to use"],
    debug: bool = False  # Optional debug flag
) -> str:
    """Load a document, split it into chunks, embed it, and upsert to Qdrant."""
    if not os.path.exists(file_path):
        return "File not found. Please provide a valid path."

    ext = os.path.splitext(file_path)[1].lower()
    try:
        # Read document
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext == ".docx":
            doc = Document(file_path)
            text = "\n".join(para.text for para in doc.paragraphs)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return "Unsupported file type. Use .pdf, .docx, or .txt."

        if debug:
            print(f"Extracted text from {file_path}:\n{text[:500]}...")  # Preview the first 500 chars

        if not text.strip():
            return "No text extracted from the document. Please check the document content."

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        docs = splitter.create_documents([text])

        if debug:
            print(f"Number of chunks: {len(docs)}")
            print(f"First chunk preview: {docs[0].page_content[:300]}...")  # Preview the first chunk

        # Initialize Qdrant client
        qdrant_client = initialize_qdrant_client()

        # Ensure collection exists
        ensure_collection_exists(qdrant_client, collection_name)

        # Prepare points for upsert
        points = []
        for doc in docs:
            vector = encode_text(doc.page_content)
            point = PointStruct(
                id=generate_unique_id(),
                vector=vector,
                payload={"text": doc.page_content}
            )
            points.append(point)

        # Upsert points into Qdrant
        response = qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        if debug:
            print(f"Successfully upserted {len(points)} documents to Qdrant collection: {collection_name}")
            print("Qdrant response:", response)

        return f"Document successfully ingested into collection: {collection_name}"

    except Exception as e:
        return f"Error during document ingestion: {e}"

def initialize_qdrant_client() -> QdrantClient:
    """Initialize and return a Qdrant client."""
    validate_env_vars()
    return QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

def validate_env_vars():
    """Ensure required environment variables are set."""
    required_vars = ["QDRANT_URL", "QDRANT_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Environment variable '{var}' is not set.")

def ensure_collection_exists(client: QdrantClient, collection_name: str):
    """Ensure the specified collection exists in Qdrant."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "default": VectorParams(
                    size=384,  # Default vector size
                    distance="Cosine"
                )
            }
        )
        print(f"Collection '{collection_name}' created in Qdrant.")
    else:
        print(f"Collection '{collection_name}' already exists.")

# Run the MCP server
if __name__ == "__main__":
    mcp.settings.port = 8201  # You can change the port if needed
    mcp.settings.sse_path = "/qdrant_connection"  # Endpoint path for testing connection
    mcp.run(transport="sse")
