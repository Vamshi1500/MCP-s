import asyncio
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os
import warnings

# Suppress resource warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# Load environment variables
load_dotenv()

# Azure OpenAI model config
API_VERSION = os.getenv("apiVersion")
API_KEY = os.getenv("apiKey")
API_BASE = os.getenv("apiBase")
MODEL_NAME = os.getenv("modelName")

# LangChain model
model = AzureChatOpenAI(
    azure_deployment=MODEL_NAME,
    api_version=API_VERSION,
    openai_api_key=API_KEY,
    azure_endpoint=API_BASE
)

# MCP client config
server_params = MultiServerMCPClient({
    "Qdrant_MCP": {
        "url": "http://localhost:8201/qdrant_docx",
        "transport": "sse"
    }
})

# Async main function
async def main():
    async with server_params as client:
        tools = client.get_tools()
        agent = create_react_agent(model, tools)

        chat_history = []  # <-- Store full conversation here

        while True:
            user_input = input("Enter your query (type 'exit' to quit): ")
            if user_input.lower() == "exit":
                print("Exiting...")
                break

            # Add user input to history
            chat_history.append(HumanMessage(content=user_input))

            # Run the agent with full history
            agent_response = await agent.ainvoke({
                "messages": chat_history
            })

            # Get the last AI message and print it
            if isinstance(agent_response, dict) and 'messages' in agent_response:
                final_message = agent_response['messages'][-1]
                if hasattr(final_message, 'content'):
                    print("Response:", final_message.content)
                    chat_history.append(AIMessage(content=final_message.content))  # <-- Store AI response
                else:
                    print("No content in the final message.")
            else:
                print("Unexpected response format:", agent_response)

# Run the script
asyncio.run(main())