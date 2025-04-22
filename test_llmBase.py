import asyncio
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import warnings

# Suppress resource warnings (optional)
warnings.filterwarnings("ignore", category=ResourceWarning)

# Load environment variables
load_dotenv()

# Azure OpenAI model configuration
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

# Define server parameters
server_params = MultiServerMCPClient({
    "Postgres_MCP": {
        "url": "http://localhost:8200/postgres_crud",
        "transport": "sse"
    }
})

# Define the main async function
async def main():
    async with server_params as client:
        # Get tools from the server
        tools = client.get_tools()

       
        # Create and run the agent
        agent = create_react_agent(model, tools)
      

        while True:
            user_input = input("Enter your query (type 'exit' to quit): ")
            if user_input.lower() == "exit":
                print("Exiting...")
                break

            # Run the agent with the user's query
            agent_response = await agent.ainvoke({
                "messages": [HumanMessage(content=user_input)]
            })

            # Extract and print the final response content
            if isinstance(agent_response, dict) and 'messages' in agent_response:
                final_message = agent_response['messages'][-1]  # Get the last message
                if hasattr(final_message, 'content'):
                    print("Response:", final_message.content)
                else:
                    print("No content in the final message.")
            else:
                print("Unexpected response format:", agent_response)

asyncio.run(main())