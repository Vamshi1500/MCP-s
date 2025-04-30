from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from typing_extensions import Annotated
import os
from mcp.server.fastmcp import FastMCP
import pdfplumber
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct
from uuid import uuid4
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import numpy as np

mcp = FastMCP("Qdrant_MCP")

@mcp.tool()
def create_qdrant_collection(
    collection_name: Annotated[str, "Name of the Qdrant collection to create"]
) -> str:
    """Creates a new collection in Qdrant with default vector settings."""

    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        # Check if collection already exists
        existing = qdrant_client.get_collections().collections
        if any(col.name == collection_name for col in existing):
            return f"Collection '{collection_name}' already exists."

        # Create collection with 768-dimensional vectors using cosine similarity
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        return f"Collection '{collection_name}' created successfully."

    except Exception as e:
        return f"Failed to create collection: {str(e)}"

@mcp.tool()
def split_file_into_chunks(
    file_path: Annotated[str, "Path to the input document (PDF, DOCX, or TXT)"]
) -> list[str]:
    """Splits a document into text chunks for embedding."""

    if not os.path.exists(file_path):
        return ["File not found."]

    ext = os.path.splitext(file_path)[1].lower()

    try:
        # Extract text
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif ext == ".docx":
            doc = Document(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            return ["Unsupported file type. Use .pdf, .docx, or .txt."]

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(text)

        return chunks if chunks else ["No content found in document."]
    except Exception as e:
        return [f"Error reading or splitting document: {str(e)}"]

def encode_text(text):
    return [0.0] * 768  # placeholder vector of size 768

# @mcp.tool()
# def upsert_chunks_to_qdrant(
#     chunks: Annotated[list[str], "List of text chunks"],
#     collection_name: Annotated[str, "Name of the Qdrant collection"]
# ) -> str:
#     """Upserts a list of text chunks into Qdrant."""

#     try:
#         qdrant_client = QdrantClient(
#             url=os.getenv("QDRANT_URL"),
#             api_key=os.getenv("QDRANT_API_KEY")
#         )

#         points = []
#         for chunk in chunks:
#             vector = encode_text(chunk)  # Replace with actual embedding
#             points.append(PointStruct(
#                 id=str(uuid4()),
#                 vector=vector,
#                 payload={"text": chunk}
#             ))

#         qdrant_client.upsert(collection_name=collection_name, points=points)
#         return f"Upserted {len(points)} chunks into collection '{collection_name}'."
#     except Exception as e:
#         return f"Upsert failed: {str(e)}"
@mcp.tool()
def upsert_chunks_to_qdrant(
    chunks: Annotated[list[str], "List of text chunks to upsert"],
    collection_name: Annotated[str, "Qdrant collection name"],
    document_name: Annotated[str, "Original document name (e.g., 'pay.docx')"]
) -> str:
    """Upserts text chunks into a Qdrant collection, tagging each chunk with the document name."""

    try:
        # Initialize the Qdrant client with environment config
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        # Prepare list of PointStructs with tagged payloads
        points = []
        for chunk in chunks:
            vector = encode_text(chunk)  # Placeholder or real embedding
            points.append(PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "document_name": document_name
                }
            ))

        # Upsert all points to the specified collection
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        return f"Upserted {len(points)} chunks from '{document_name}' into collection '{collection_name}'."

    except Exception as e:
        return f"Upsert failed: {str(e)}"

########### Search Functionality ###########
def encode_text(text):
    """Generate embeddings using SentenceTransformer model."""
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dimensional embeddings
    return model.encode(text).tolist()

@mcp.tool()
def semantic_search_qdrant(
    query: Annotated[str, "Search query text"],
    collection_name: Annotated[str, "Name of the Qdrant collection to search"],
    limit: Annotated[int, "Maximum number of results to return"] = 5
) -> list:
    """Searches for semantically similar content using the query text."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Generate embedding for the query
        query_vector = encode_text(query)
        
        # Perform semantic search
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
        
        # Format results
        formatted_results = [
            {
                "id": str(point.id),
                "score": round(point.score, 4),
                "text": point.payload.get("text", ""),
                "document_name": point.payload.get("document_name", "unknown")
            }
            for point in results
        ]
        
        return formatted_results
    
    except Exception as e:
        return [{"error": f"Search failed: {str(e)}"}]
    
@mcp.tool()
def filter_search_by_document(
    query: Annotated[str, "Search query text"],
    document_name: Annotated[str, "Document name to filter by"],
    collection_name: Annotated[str, "Name of the Qdrant collection to search"],
    limit: Annotated[int, "Maximum number of results to return"] = 5
) -> list:
    """Searches for content within a specific document."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Generate embedding for the query
        query_vector = encode_text(query)
        
        # Create filter for specific document
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name)
                )
            ]
        )
        
        # Perform filtered search
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=document_filter,
            limit=limit,
            with_payload=True
        )
        
        # Format results
        formatted_results = [
            {
                "id": str(point.id),
                "score": round(point.score, 4),
                "text": point.payload.get("text", ""),
                "document_name": point.payload.get("document_name", "unknown")
            }
            for point in results
        ]
        
        return formatted_results
    
    except Exception as e:
        return [{"error": f"Filtered search failed: {str(e)}"}]

@mcp.tool()
def list_documents_in_collection(
    collection_name: Annotated[str, "Name of the Qdrant collection"]
) -> list:
    """Lists all unique document names in a collection."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Scroll through collection to find all document names
        # We'll set a reasonable limit but this might need adjustment for large collections
        results = qdrant_client.scroll(
            collection_name=collection_name,
            limit=10000,
            with_payload=["document_name"],
            with_vectors=False
        )[0]  # First element is list of points, second is next page offset
        
        # Extract unique document names
        document_names = set()
        for point in results:
            doc_name = point.payload.get("document_name")
            if doc_name:
                document_names.add(doc_name)
        
        return sorted(list(document_names))
    
    except Exception as e:
        return [f"Error listing documents: {str(e)}"]
    
@mcp.tool()
def extract_document_content(
    document_name: Annotated[str, "Document name to extract content from"],
    collection_name: Annotated[str, "Name of the Qdrant collection"]
) -> str:
    """Extracts and concatenates all content from a specific document."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Create filter for specific document
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name)
                )
            ]
        )
        
        # Get all chunks from this document (using a dummy vector for the scroll operation)
        results = qdrant_client.scroll(
            collection_name=collection_name,
            filter=document_filter,
            limit=10000,
            with_payload=["text"],
            with_vectors=False
        )[0]
        
        # Extract and join text
        text_chunks = [point.payload.get("text", "") for point in results]
        
        if not text_chunks:
            return f"No content found for document '{document_name}'."
        
        return "\n\n".join(text_chunks)
    
    except Exception as e:
        return f"Error extracting document content: {str(e)}"

if __name__ == "__main__":
    mcp.settings.port = 8201  # You can change the port if needed
    mcp.settings.sse_path = "/qdrant_docx"  # Endpoint path for testing connection
    mcp.run(transport="sse")


# DOWNLOAD_DIR = "download_files"
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# # This function will create a file from Qdrant content when needed
# def create_file_from_qdrant(collection_name, document_name):
#     file_path = os.path.join(DOWNLOAD_DIR, f"{collection_name}_{document_name}")
    
#     try:
#         # Initialize Qdrant client
#         qdrant_client = QdrantClient(
#             url=os.getenv("QDRANT_URL"),
#             api_key=os.getenv("QDRANT_API_KEY")
#         )
        
#         # Define filter for the specific document
#         document_filter = Filter(
#             must=[
#                 FieldCondition(
#                     key="document_name",
#                     match=MatchValue(value=document_name)
#                 )
#             ]
#         )
        
#         # Get document content
#         results = qdrant_client.scroll(
#             collection_name=collection_name,
#             scroll_filter=document_filter,
#             limit=10000,
#             with_payload=True,
#             with_vectors=False
#         )[0]
        
#         if not results:
#             return None
        
#         # Extract text chunks and combine
#         chunks = []
#         for point in results:
#             if "text" in point.payload:
#                 chunks.append(point.payload["text"])
        
#         # Write to file
#         with open(file_path, 'w', encoding='utf-8') as f:
#             f.write("\n\n".join(chunks))
        
#         return file_path
#     except Exception as e:
#         print(f"Error creating file: {str(e)}")
#         traceback.print_exc()
#         return None

# @mcp.tool()
# def download_document(
#     document_name: Annotated[str, "Name of document to download"],
#     collection_name: Annotated[str, "Name of the collection containing the document"]
# ) -> str:
#     """Creates a downloadable file from document content in Qdrant."""
    
#     try:
#         # Create the file
#         file_path = create_file_from_qdrant(collection_name, document_name)
        
#         if not file_path or not os.path.exists(file_path):
#             return f"Document '{document_name}' not found in collection '{collection_name}' or couldn't be processed."
        
#         # Return success with the file path
#         return f"Document created successfully and saved at: {file_path}\n\nYou can access this file directly on the server."
    
#     except Exception as e:
#         return f"Error downloading document: {str(e)}"
