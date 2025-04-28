from typing_extensions import Annotated
import os
from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from uuid import uuid4
from qdrant_client.models import PointStruct, VectorParams, Distance, PayloadSchemaType
import pdfplumber
from docx import Document as DocxDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
import traceback

# Create MCP instance
mcp = FastMCP("Qdrant_MCP")

# Placeholder embedding function - replace with proper embedding model later
def encode_text(text):
    return [0.0] * 768  # placeholder vector of size 768

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

        # First create collection with standard settings
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
        # Then create the payload index separately
        try:
            qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="document_name",
                field_schema="keyword"
            )
        except Exception as index_error:
            return f"Collection created but index creation failed: {str(index_error)}"
            
        return f"Collection '{collection_name}' created successfully with document_name index."

    except Exception as e:
        return f"Failed to create collection: {str(e)}"

@mcp.tool()
def create_payload_index(
    collection_name: Annotated[str, "Name of the collection to update"],
    field_name: Annotated[str, "Name of the field to index"]
) -> str:
    """Creates a payload index on the specified field."""
    try:
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema="keyword"
        )
        
        return f"Successfully created index on field '{field_name}' in collection '{collection_name}'."
    except Exception as e:
        return f"Failed to create index: {str(e)}"

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
            doc = DocxDocument(file_path)
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
        # Print more detailed error for debugging
        print(f"Error in list_documents_in_collection: {str(e)}")
        print(traceback.format_exc())
        return [f"Error listing documents: {str(e)}"]

@mcp.tool()
def retrieve_document_content(
    document_name: Annotated[str, "Document name to retrieve"],
    collection_name: Annotated[str, "Name of the Qdrant collection"]
) -> str:
    """Retrieves all text chunks from a specific document and combines them."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Define filter for the specific document
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name)
                )
            ]
        )
        
        # Scroll through all points with this document name
        results = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=document_filter,
            limit=10000,  # High limit to get all chunks
            with_payload=True,  # Get the full payload including text
            with_vectors=False  # No need for vectors
        )[0]  # First element is points, second is next_page_offset
        
        if not results:
            return f"No content found for document '{document_name}' in collection '{collection_name}'."
        
        # Extract text from each chunk and join them
        chunks = []
        for point in results:
            if point.payload and "text" in point.payload:
                chunks.append(point.payload["text"])
        
        # Join all chunks with double newlines
        full_content = "\n\n".join(chunks)
        
        return full_content if full_content else f"Document '{document_name}' exists but contains no text."
    
    except Exception as e:
        # Print more detailed error for debugging
        print(f"Error in retrieve_document_content: {str(e)}")
        print(traceback.format_exc())
        return f"Error retrieving document content: {str(e)}"

@mcp.tool()
def semantic_search(
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
        
        # Generate embedding for the query (placeholder)
        query_vector = encode_text(query)
        
        # Perform semantic search
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
        
        # Format results
        formatted_results = []
        for point in results:
            formatted_results.append({
                "id": str(point.id),
                "score": round(point.score, 4),
                "text": point.payload.get("text", ""),
                "document_name": point.payload.get("document_name", "unknown")
            })
        
        return formatted_results
    
    except Exception as e:
        print(f"Error in semantic_search: {str(e)}")
        print(traceback.format_exc())
        return [{"error": f"Search failed: {str(e)}"}]

@mcp.tool()
def delete_document(
    document_name: Annotated[str, "Name of document to delete"],
    collection_name: Annotated[str, "Name of the Qdrant collection"]
) -> str:
    """Deletes all chunks belonging to a specific document."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Define filter for the specific document
        document_filter = Filter(
            must=[
                FieldCondition(
                    key="document_name",
                    match=MatchValue(value=document_name)
                )
            ]
        )
        
        # Delete points with this document name
        operation_result = qdrant_client.delete(
            collection_name=collection_name,
            points_selector=document_filter
        )
        
        return f"Successfully deleted document '{document_name}' from collection '{collection_name}'."
    
    except Exception as e:
        return f"Error deleting document: {str(e)}"

@mcp.tool()
def delete_qdrant_collection(
    collection_name: Annotated[str, "Name of the Qdrant collection to delete"]
) -> str:
    """Deletes an entire collection from Qdrant."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Check if collection exists before attempting to delete
        existing = qdrant_client.get_collections().collections
        if not any(col.name == collection_name for col in existing):
            return f"Collection '{collection_name}' does not exist."
        
        # Delete the collection
        qdrant_client.delete_collection(collection_name=collection_name)
        
        return f"Collection '{collection_name}' has been successfully deleted."
    
    except Exception as e:
        return f"Failed to delete collection: {str(e)}"
    
@mcp.tool()
def list_collections_with_documents() -> dict:
    """Lists all collections in the Qdrant database along with documents in each collection."""
    
    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Get all collections
        collections_info = qdrant_client.get_collections()
        collection_names = [col.name for col in collections_info.collections]
        
        if not collection_names:
            return {"status": "No collections found."}
        
        # Create a dictionary to store collection -> documents mapping
        collections_with_documents = {}
        
        # For each collection, get the unique document names
        for collection_name in collection_names:
            try:
                # Scroll through collection to find all document names
                results = qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=10000,
                    with_payload=["document_name"],
                    with_vectors=False
                )[0]
                
                # Extract unique document names
                document_names = set()
                for point in results:
                    doc_name = point.payload.get("document_name")
                    if doc_name:
                        document_names.add(doc_name)
                
                collections_with_documents[collection_name] = sorted(list(document_names))
                
            except Exception as collection_error:
                collections_with_documents[collection_name] = f"Error retrieving documents: {str(collection_error)}"
        
        return collections_with_documents
    
    except Exception as e:
        print(f"Error in list_collections_with_documents: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Error listing collections: {str(e)}"}
    
if __name__ == "__main__":
    mcp.settings.port = 8201  # You can change the port if needed
    mcp.settings.sse_path = "/qdrant_docx"  # Endpoint path for testing connection
    mcp.run(transport="sse")