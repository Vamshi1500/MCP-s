from mcp.server.fastmcp import FastMCP
from typing import Annotated
import os
from docx import Document  
import pdfplumber

# Create MCP instance
mcp = FastMCP("Docx_Processing_MCP")

# Define the MCP tool for DOCX file processing
@mcp.tool()
def analyze_docx_file(
    file_path: Annotated[str, "Path to the DOCX file to analyze"]
) -> str:
    """Analyze a DOCX file and extract its content."""
    try:
        # Check if the file exists and is a valid DOCX file
        if not os.path.exists(file_path) or not file_path.lower().endswith('.docx'):
            return "Invalid file path or file is not a DOCX file. Please provide a valid DOCX file path."

        # Process the DOCX file
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])

        # Return first 500 characters of the content for preview
        return f"DOCX file content:\n\n{content[:500]}..."  # Show a preview of the content

    except Exception as e:
        return f"Error reading DOCX file: {e}"

@mcp.tool()
def analyze_pdf_file(
    file_path: Annotated[str, "Full path to the PDF file to analyze"]
) -> str:
    """Extract and analyze text from a PDF file using pdfplumber."""
    try:
        if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
            return "Invalid file path or file is not a PDF."

        content = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                content += page.extract_text() or ""
        
        if not content.strip():
            return "No text could be extracted from the PDF."

        return f"Extracted PDF Content:\n\n{content[:500]}..."  # Show snippet

    except Exception as e:
        return f"Error processing PDF file: {e}"
    
if __name__ == "__main__":
    mcp.settings.port = 8201
    mcp.settings.sse_path = "/doc_analyze"
    mcp.run(transport="sse")