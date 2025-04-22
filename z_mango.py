from pymongo import MongoClient             # pymongo driver :contentReference[oaicite:1]{index=1}
from bson import ObjectId
from mcp.server.fastmcp import FastMCP      # core server class :contentReference[oaicite:2]{index=2}
from mcp.server.fastmcp.prompts import Prompt              # Prompt builder :contentReference[oaicite:3]{index=3}
from mcp.server.fastmcp.prompts.base import PromptArgument # Prompt argument spec :contentReference[oaicite:4]{index=4}

# def init_state(state):
#     """Connect to MongoDB and store handle."""
#     client = MongoClient("mongodb://localhost:27017")   # connect via pymongo :contentReference[oaicite:5]{index=5}
#     state["db"] = client["users"]
client=MongoClient("mongodb://localhost:27017")   # connect via pymongo :contentReference[oaicite:5]{index=5}
db=client["users"]

mcp = FastMCP()            # instantiate server :contentReference[oaicite:6]{index=6}


# ---------------------
# 2. Resource: List All Documents
# ---------------------

@mcp.tool()
def create_collection(collection_name: str) -> dict:
    """
    Create a collection in the database.
    """
    try:
        db.create_collection(collection_name)
        return {"status": "success", "message": f"Collection '{collection_name}' created successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
def insert_doc(collection: str, document: dict) -> dict:
    """
    Insert a document into the specified collection.
    """
    try:
        res = db[collection].insert_one(document)
        return {"status": "success", "inserted_id": str(res.inserted_id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def find_docs(collection: str, filter: dict) -> list:
    """
    Find documents matching the filter in the specified collection.
    """
    try:
        docs = list(db[collection].find(filter))
        for d in docs:
            d["_id"] = str(d["_id"])
        return {"status": "success", "data": docs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def list_all_items(collection: str) -> list:
    """
    List all documents in the specified collection.
    """
    try:
        docs = list(db[collection].find({}))
        for d in docs:
            d["_id"] = str(d["_id"])
        return {"status": "success", "data": docs}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@mcp.tool()
def update_docs(collection: str, filter: dict, update: dict) -> dict:
    """
    Update documents matching the filter in the specified collection.
    """
    try:
        res = db[collection].update_many(filter, {"$set": update})
        return {"status": "success", "matched": res.matched_count, "modified": res.modified_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def delete_docs(collection: str, filter: dict) -> dict:
    """
    Delete documents matching the filter in the specified collection.
    """
    try:
        res = db[collection].delete_many(filter)
        return {"status": "success", "deleted": res.deleted_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


    
if __name__ == "__main__":
    # stdio (default, used by `mcp run`)
    # import uvicorn
    # uvicorn.run(app=mcp.sse_app(), host="0.0.0.0", port=8002)  
    # mcp.run() 
    #                                           # :contentReference[oaicite:14]{index=14}
    # mcp.settings.port=8002
    # mcp.settings.sse_path= "/sse"         # SSE path for the server
    # Run the MCP server
    mcp.run(transport="stdio")