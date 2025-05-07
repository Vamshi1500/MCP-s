from typing_extensions import Annotated, List
from mcp.server.fastmcp import FastMCP
from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize
import re
from statistics import mean
import traceback
import logging
from typing_extensions import Annotated, List
import os
import docx
import pdfplumber
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sentiment_analyzer")

# Ensure punkt is available
nltk.download("punkt", quiet=True)
nltk.download('punkt_tab', quiet=True)

# Set up MCP instance - IMPORTANT: Using Qdrant_MCP to match the client configuration
mcp = FastMCP("Qdrant_MCP")

# Load sentiment analysis pipeline with explicit model to avoid warnings
try:
    sentiment_pipeline = pipeline(
        "sentiment-analysis", 
        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english"
    )
    logger.info("Sentiment analysis pipeline loaded successfully")
except Exception as e:
    logger.error(f"Error loading sentiment pipeline: {str(e)}")
    sentiment_pipeline = None

def preprocess_text(text):
    """Clean and prepare text for analysis."""
    try:
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Handle URLs (replace with placeholder to avoid sentiment bias)
        text = re.sub(r'https?://\S+', '[URL]', text)
        return text
    except Exception as e:
        logger.error(f"Error in preprocess_text: {str(e)}")
        return text

@mcp.tool()
def analyze_sentiment(
    text: Annotated[str, "Text input for sentiment analysis"]
) -> dict:
    """Performs sentiment analysis on the given text."""
    logger.info(f"Analyzing sentiment for text: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    try:
        if not sentiment_pipeline:
            return {"error": "Sentiment pipeline not available"}
            
        cleaned_text = preprocess_text(text)
        sentences = sent_tokenize(cleaned_text)
        logger.info(f"Split into {len(sentences)} sentences")
        
        # For single short text, use simple analysis
        if len(sentences) <= 1:
            result = sentiment_pipeline(cleaned_text)[0]
            logger.info(f"Single sentence result: {result}")
            response = {
                "label": result["label"],
                "sentiment": result["label"].lower(),
                "confidence": round(result["score"], 3),
                "summary": f"Sentiment is {result['label'].lower()} with {result['score'] * 100:.1f}% confidence."
            }
            logger.info(f"Returning single sentence response: {response}")
            return response
        
        # For multiple sentences, do sentence-by-sentence analysis
        results = sentiment_pipeline(sentences)
        logger.info(f"Multiple sentence results: {results}")
        
        # Count positive and negative sentences
        label_counts = {"POSITIVE": 0, "NEGATIVE": 0}
        confidence_scores = {"POSITIVE": [], "NEGATIVE": []}
        sentence_analyses = []
        
        for sent, res in zip(sentences, results):
            label = res["label"]
            confidence = round(res["score"], 3)
            
            label_counts[label] += 1
            confidence_scores[label].append(confidence)
            
            sentence_analyses.append({
                "text": sent,
                "sentiment": label.lower(),
                "confidence": confidence
            })
        
        # Calculate percentages
        total_sentences = len(sentences)
        positive_percentage = (label_counts["POSITIVE"] / total_sentences) * 100 if total_sentences > 0 else 0
        negative_percentage = (label_counts["NEGATIVE"] / total_sentences) * 100 if total_sentences > 0 else 0
        
        # Determine if it's a mixed sentiment
        is_mixed = label_counts["POSITIVE"] > 0 and label_counts["NEGATIVE"] > 0
        
        if is_mixed:
            # Format a summary for mixed sentiment
            if positive_percentage > negative_percentage:
                overall = "mixed (leaning positive)"
            elif negative_percentage > positive_percentage:
                overall = "mixed (leaning negative)"
            else:
                overall = "mixed (balanced)"
                
            summary = (f"Mixed sentiment detected: {positive_percentage:.1f}% positive and "
                      f"{negative_percentage:.1f}% negative.")
            
            formatted_analysis = " | ".join([
                f'"{s["text"]}" → {s["sentiment"]} ({s["confidence"] * 100:.1f}%)' 
                for s in sentence_analyses
            ])
            
            response = {
                "is_mixed": True,
                "overall_sentiment": overall,
                "positive_percentage": round(positive_percentage, 1),
                "negative_percentage": round(negative_percentage, 1),
                "positive_sentences": label_counts["POSITIVE"],
                "negative_sentences": label_counts["NEGATIVE"],
                "summary": summary,
                "sentence_analysis": sentence_analyses,
                "formatted_analysis": formatted_analysis
            }
        else:
            # Single sentiment (all positive or all negative)
            if label_counts["POSITIVE"] > 0:
                overall = "positive"
                confidence = mean(confidence_scores["POSITIVE"])
            else:
                overall = "negative"
                confidence = mean(confidence_scores["NEGATIVE"])
                
            response = {
                "overall_sentiment": overall,
                "overall_confidence": round(confidence, 3),
                "summary": f"The overall sentiment of the text is {overall}, with a high confidence of {confidence * 100:.1f}%."
            }
        
        logger.info(f"Returning response: {response}")
        return response
    
    except Exception as e:
        error_msg = f"Error in analyze_sentiment: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"error": error_msg}

@mcp.tool()
def analyze_sentiment_detailed(
    text: Annotated[str, "Text input to analyze sentiment sentence-by-sentence"]
) -> dict:
    """Analyzes sentiment sentence-by-sentence and returns summary + explanation."""
    logger.info("analyze_sentiment_detailed called, redirecting to main function")
    # Just redirect to the main analyze_sentiment function which now does detailed analysis
    return analyze_sentiment(text)

@mcp.tool()
def batch_analyze_sentiment(
    texts: Annotated[List[str], "List of text inputs for sentiment analysis"]
) -> List[dict]:
    """Performs sentiment analysis on multiple texts."""
    logger.info(f"Batch analyzing {len(texts)} texts")
    try:
        results = []
        for text in texts:
            analysis = analyze_sentiment(text)
            results.append({
                "text": text[:50] + "..." if len(text) > 50 else text,
                "sentiment": analysis.get("overall_sentiment", analysis.get("sentiment", "unknown")),
                "summary": analysis.get("summary", "No summary available.")
            })
        logger.info(f"Batch analysis complete, returning {len(results)} results")
        return results
    except Exception as e:
        error_msg = f"Error in batch_analyze_sentiment: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return [{"error": error_msg}]
    
# Add these imports to your existing imports
# No need to duplicate existing imports like FastMCP, pipeline, etc.

def extract_text_from_file(file_path):
    """Extract text content from a file (TXT or DOCX)."""
    logger.info(f"Extracting text from file: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return f"Error: File not found: {file_path}"
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract text based on file type
        if file_ext == '.txt':
            logger.info("Reading TXT file")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with a different encoding if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
                    
        elif file_ext == '.docx':
            logger.info("Reading DOCX file")
            doc = docx.Document(file_path)
            return '\n'.join(para.text for para in doc.paragraphs)
            
        elif file_ext == '.pdf':
            logger.info("Reading PDF file")
            text_content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text = page.extract_text()
                    if extracted_text:
                        text_content.append(extracted_text)
            return '\n\n'.join(text_content)
            
        else:
            error_msg = f"Unsupported file type: {file_ext}. Only .txt, .docx, and .pdf are supported."
            logger.error(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"Error extracting text from file: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg

@mcp.tool()
def analyze_sentiment_from_file(
    file_path: Annotated[str, "Path to the text file (.txt), Word document (.docx), or PDF file (.pdf) to analyze"]
) -> dict:
    """
    Reads text from a file and performs sentiment analysis on its content.
    Supports .txt, .docx, and .pdf files.
    """
    logger.info(f"Analyzing sentiment from file: {file_path}")
    
    try:
        # Extract text from the file
        text = extract_text_from_file(file_path)
        
        # Check if an error was returned
        if text.startswith("Error:"):
            return {"error": text}
            
        # Get file name for reporting
        file_name = os.path.basename(file_path)
        
        # Perform sentiment analysis on the extracted text
        sentiment_results = analyze_sentiment(text)
        
        # Add file information to the results
        sentiment_results["file_name"] = file_name
        sentiment_results["file_path"] = file_path
        sentiment_results["text_length"] = len(text)
        sentiment_results["word_count"] = len(text.split())
        
        return sentiment_results
        
    except Exception as e:
        error_msg = f"Error in analyze_sentiment_from_file: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return {"error": error_msg, "file_path": file_path}

@mcp.tool()
def batch_analyze_sentiment_from_files(
    file_paths: Annotated[List[str], "List of file paths (.txt, .docx, or .pdf) to analyze"]
) -> List[dict]:
    """
    Reads text from multiple files and performs sentiment analysis on each.
    Supports .txt, .docx, and .pdf files.
    """
    logger.info(f"Batch analyzing sentiment from {len(file_paths)} files")
    
    results = []
    for file_path in file_paths:
        try:
            # Analyze sentiment for each file
            analysis = analyze_sentiment_from_file(file_path)
            
            # Add to results list
            results.append({
                "file_name": os.path.basename(file_path),
                "sentiment": analysis.get("overall_sentiment", analysis.get("sentiment", "unknown")),
                "summary": analysis.get("summary", "No summary available.")
            })
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            results.append({
                "file_name": os.path.basename(file_path),
                "error": error_msg
            })
    
    return results

@mcp.tool()
def analyze_document_content_from_qdrant(
    document_name: Annotated[str, "Name of the document in Qdrant"],
    collection_name: Annotated[str, "Name of the Qdrant collection"]
) -> dict:
    """
    Retrieves document content from Qdrant and performs sentiment analysis on it.
    
    Note: This function requires the Qdrant document management system to be 
    running and accessible with the retrieve_document_content function.
    """
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        logger.info(f"Analyzing sentiment from Qdrant document: {document_name}")
        
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
        )[0]
        
        if not results:
            return {"error": f"No content found for document '{document_name}' in collection '{collection_name}'."}
        
        # Extract text from each chunk and join them
        chunks = []
        for point in results:
            if point.payload and "text" in point.payload:
                chunks.append(point.payload["text"])
        
        # Join all chunks with double newlines
        full_content = "\n\n".join(chunks)
        
        if not full_content:
            return {"error": f"Document '{document_name}' exists but contains no text."}
            
        # Perform sentiment analysis on the document content
        sentiment_results = analyze_sentiment(full_content)
        
        # Add document information to the results
        sentiment_results["document_name"] = document_name
        sentiment_results["collection_name"] = collection_name
        sentiment_results["text_length"] = len(full_content)
        sentiment_results["word_count"] = len(full_content.split())
        
        return sentiment_results
        
    except ImportError:
        return {"error": "Qdrant client not available. Please install with pip install qdrant-client"}
    except Exception as e:
        error_msg = f"Error analyzing document from Qdrant: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return {"error": error_msg}



if __name__ == "__main__":
    
    mcp.settings.port = 8202
    mcp.settings.sse_path = "/sentiment_analysis"
    
    logger.info("Starting MCP server with port 8202 and path /sentiment_analysis")
    mcp.run(transport="sse")