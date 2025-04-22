from mcp.server.fastmcp import FastMCP
from typing import Annotated
from docx import Document
from io import BytesIO
import zipfile

mcp = FastMCP("My_Demo_Server")

@mcp.tool()
def greet(name: str) -> str:
    """Greet the user with their name
    accept input as - 'greet name'"""
    return f"Hello, {name}!"

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers
    example : add 2 3"""
    return a + b

@mcp.tool()
def echo(text: str) -> str:
    return f"You said: {text}"

@mcp.tool()
def read_docx(file: Annotated[bytes, "Upload a .docx file"]) -> str:
    """Read the attached file
    Example: read (attached file)"""
    
    try:
        # checks if the file is a valid zip file (which .docx is)
        if not zipfile.is_zipfile(BytesIO(file)):
            # if uploaded id not a valid zip file then tries to decode it as plain text
            try:
                return file.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    return file.decode('latin-1')  
                except Exception:
                    return "File is not a valid .docx file and could not be decoded as text."
        
        # if it's a valid zip then proceeds to read the file 
        doc = Document(BytesIO(file))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text or "No text found in the document."
    except Exception as e:
        return f"Error processing the file: {str(e)}"
    
if __name__ == "__main__":
    mcp.settings.port=8000
    mcp.settings.sse_path= "/doc_read"
    mcp.run(transport="sse")