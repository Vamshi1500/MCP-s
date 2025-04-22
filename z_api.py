from fastapi import FastAPI
from pydantic import BaseModel
from z import greet, add, echo  # Import tools from z.py
import uvicorn

app = FastAPI()

# Pydantic models for input data validation
class GreetRequest(BaseModel):
    name: str

class AddRequest(BaseModel):
    a: int
    b: int

class EchoRequest(BaseModel):
    text: str

@app.post("/tools/greet")
async def greet_tool(request: GreetRequest):
    """
    API endpoint for the greet tool.
    """
    result = greet(request.name)  # Call the greet tool
    return {"result": result}

@app.post("/tools")
async def add_tool(request: AddRequest):
    """
    API endpoint for the add tool.
    """
    result = add(request.a, request.b)  # Call the add tool
    return {"result": result}

@app.post("/tools/echo")
async def echo_tool(request: EchoRequest):
    """
    API endpoint for the echo tool.
    """
    result = echo(request.text)  # Call the echo tool
    return {"result": result}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8100)