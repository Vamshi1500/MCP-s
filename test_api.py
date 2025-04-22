from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)
load_dotenv()

# FastAPI setup
app = FastAPI()

# Azure OpenAI setup
API_VERSION = os.getenv("apiVersion")
API_KEY = os.getenv("apiKey")
API_BASE = os.getenv("apiBase")
MODEL_NAME = os.getenv("modelName")

model = AzureChatOpenAI(
    azure_deployment=MODEL_NAME,
    api_version=API_VERSION,
    openai_api_key=API_KEY,
    azure_endpoint=API_BASE
)

# MCP tool client (SSE version)
server_params = MultiServerMCPClient({
    # "My_Demo_Server": {
    #     "url": "http://localhost:8000/doc_read", 
    #     "transport": "sse"
    # },  
    "Map_MCP_Server": {
        "url": "http://localhost:8001/country_map",
        "transport": "sse"
    },
    "Auto_Location_Link_Tool": {
        "url": "http://localhost:8002/location_map",  
        "transport": "sse"
    },
})

# Request schema
class MessageInput(BaseModel):
    message: str

@app.post("/ask")
async def ask_agent(request: MessageInput):
    async with server_params as client:
        tools = client.get_tools()
        agent = create_react_agent(model, tools)
        agent_response = await agent.ainvoke({
            "messages": [HumanMessage(content=request.message)]
        })

        final_message = agent_response["messages"][-1]
        return {"reply": final_message.content}
