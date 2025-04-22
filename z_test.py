import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import warnings
from langchain_mcp_adapters.client import MultiServerMCPClient

warnings.filterwarnings("ignore", category=ResourceWarning)
load_dotenv()

# Model config from .env
API_VERSION = os.getenv("apiVersion")
API_KEY = os.getenv("apiKey")
API_BASE = os.getenv("apiBase")
MODEL_NAME = os.getenv("modelName")

# LangChain Model
model = AzureChatOpenAI(
    azure_deployment=MODEL_NAME,
    api_version=API_VERSION,
    openai_api_key=API_KEY,
    azure_endpoint=API_BASE
)

# Server to run your MCP tools
server_params = MultiServerMCPClient(
    {
        # "My_Demo_Server": {
        #     "url": "http://localhost:8000/doc_read",  # Connect to the server running on port 8000
        #     "transport": "sse"
        # },
        # "Map_MCP_Server": {
        #     "url": "http://localhost:8001/country_map",  # Connect to the server running on port 8001
        #     "transport": "sse"
        # },
        # "Auto_Location_Link_Tool": {
        #     "url": "http://localhost:8002/location_map",  # Connect to the server running on port 8002
        #     "transport": "sse"
        # }
        "Postgres_MCP":{
            "url": "http://localhost:8003/postgres_crud"
        }
    }
)

# FastAPI setup
app = FastAPI()

# Request schema
class MessageInput(BaseModel):
    message: str

# Define API endpoint
# @app.post("/ask")
# async def ask_agent(request: MessageInput):
#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             tools = await load_mcp_tools(session)
#             agent = create_react_agent(model, tools)
#             agent_response = await agent.ainvoke({
#                 "messages": [HumanMessage(content=request.message)]
#             })

#             final_reply = agent_response["messages"][-1].content
#             return {"reply": final_reply}
@app.post("/ask")
async def ask_agent(request: MessageInput):
    tools = server_params.get_tools()  # no await here!
    agent = create_react_agent(model, tools)
    agent_response = await agent.ainvoke({
        "messages": [HumanMessage(content=request.message)]
    })

    final_reply = agent_response["messages"][-1].content
    return {"reply": final_reply}
