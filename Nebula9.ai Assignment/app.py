import os
import subprocess
import re
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

# Importing Hugging Face Transformers for LLaMA
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "upload"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variable for LLM model to avoid reloading on every request
CODE_INTERPRETER = None

def initialize_code_interpreter():
    """
    Initialize BART for summarization and suggestions.
    """
    global CODE_INTERPRETER
    try:
        import torch  # Ensure torch is imported within the function

        model_name = "facebook/bart-large-cnn"  # BART model fine-tuned for summarization
        print("Loading BART model for summarization. This may take a moment...")

        # Create a pipeline for summarization
        CODE_INTERPRETER = pipeline(
            "summarization",
            model=model_name,
            device=0 if torch.cuda.is_available() else -1  # Use GPU if available, otherwise CPU
        )
        print("BART Model Loaded Successfully!")
    except ImportError as e:
        print(f"PyTorch is not installed or cannot be imported. Error: {e}")
    except Exception as e:
        print(f"Error loading BART model: {e}")
        CODE_INTERPRETER = None



def preprocess_static_analysis(static_analysis_result):
    """
    Clean and preprocess static analysis results:
    - Extract everything after the second colon.
    - Remove content inside parentheses.
    - Remove warning codes (e.g., W0108, C0301).
    """
    relevant_lines = []
    for line in static_analysis_result.split("\n"):
        # Match lines with issues and extract everything after the second colon
        parts = line.split(":", maxsplit=3)
        if len(parts) > 2:  # Ensure there are enough parts
            issue_description = parts[3].strip()  # Take everything after the second colon
            
            # Remove content inside parentheses
            issue_description = re.sub(r"\(.*?\)", "", issue_description).strip()
            
            # Remove warning codes (e.g., W0108)
            issue_description = re.sub(r"^[A-Z]\d{4}:\s*", "", issue_description).strip()
            
            relevant_lines.append(issue_description)
    
    # Limit to first 30 cleaned lines for brevity
    return "\n".join(relevant_lines[:30])

def llm_static_analysis_summary(static_analysis_result):
    """
    Use BART to summarize preprocessed static analysis results and suggest improvements.
    """
    if CODE_INTERPRETER is None:
        return "LLM model not available for summarizing static analysis results."

    try:
        # Preprocess the input
        filtered_results = preprocess_static_analysis(static_analysis_result)

        if not filtered_results:
            return "No relevant warnings or errors found in the static analysis results."

        # Generate summary using BART
        summary = CODE_INTERPRETER(
            filtered_results, 
            max_length=150,  # Adjust based on desired summary length
            min_length=30, 
            do_sample=False  # Ensure deterministic output
        )
        return summary[0]['summary_text']

    except Exception as e:
        return f"Error generating summary: {str(e)}"


def analyze_code(file_path):
    """
    Perform static code analysis based on file type.
    """
    try:
        # Supported static analysis tools for different file types
        if file_path.endswith(".py"):
            result = subprocess.run(["pylint", "--output-format=text", file_path], 
                                    capture_output=True, text=True, timeout=30)
            return result.stdout
        elif file_path.endswith(".js"):
            result = subprocess.run(["eslint", file_path], 
                                    capture_output=True, text=True, timeout=30)
            return result.stdout
        elif file_path.endswith(".cpp"):
            result = subprocess.run(["cppcheck", "--enable=all", file_path], 
                                    capture_output=True, text=True, timeout=30)
            return result.stdout
        elif file_path.endswith(".html"):
            result = subprocess.run(["tidy", "-errors", "-quiet", file_path], 
                                    capture_output=True, text=True, timeout=30)
            return result.stdout
        else:
            return "Unsupported file type for static analysis"
    except subprocess.TimeoutExpired:
        return f"{os.path.basename(file_path)} analysis timed out"
    except Exception as e:
        return f"Error during static analysis: {str(e)}"

def analyze_text_file(file_path):
    """
    Analyze and summarize the content of .doc, .txt, and .pdf files using BART.
    Automatically wraps lines after 150 characters for better readability.
    """
    try:
        # Extract content based on file type
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        elif file_path.endswith(".docx"):
            from docx import Document  # Import for .docx files
            doc = Document(file_path)
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file_path.endswith(".pdf"):
            from PyPDF2 import PdfReader  # Import for .pdf files
            reader = PdfReader(file_path)
            content = "\n".join(page.extract_text() for page in reader.pages)

        else:
            return "Unsupported text file type for analysis."

        # Dynamically wrap lines to a specified width
        def wrap_text(text, width=150):
            """
            Wrap text dynamically to a specified width.
            """
            import textwrap
            return "\n".join(textwrap.wrap(text, width))

        # Wrap the extracted content
        wrapped_content = wrap_text(content)

        # Use BART for summarization
        if CODE_INTERPRETER is None:
            return "Summarization model not available for text file analysis."

        summary = CODE_INTERPRETER(
            wrapped_content, 
            max_length=300,  # Adjust summary length as needed
            min_length=50, 
            do_sample=False
        )

        # Wrap the summary text
        final_summary = wrap_text(summary[0]['summary_text'])
        return final_summary  # Keep line breaks (\n) for plain-text rendering

    except Exception as e:
        return f"Error during text file analysis: {str(e)}"

def categorize_static_analysis(static_analysis_result):
    """
    Categorize static analysis results into Readability, Code Quality, and Error categories.
    """
    categories = {"Readability": [], "Code Quality": [], "Error": []}

    for line in static_analysis_result.split("\n"):
        # Lowercase the line for easier matching
        lower_line = line.lower()

        # Check categories
        if "line too long" in lower_line or "readable" in lower_line:
            categories["Readability"].append(line)
        elif "unused" in lower_line or "redundant" in lower_line or "code quality" in lower_line:
            categories["Code Quality"].append(line)
        elif "error" in lower_line or "undefined" in lower_line:
            categories["Error"].append(line)

    return categories

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """
    File upload and analysis logic.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request."})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."})

    # Save the uploaded file
    filename = secure_filename(file.filename)
    name, extension = os.path.splitext(filename)
    unique_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    try:
        if extension in [".py", ".js", ".cpp", ".html"]:
            # Static code analysis
            static_analysis_result = analyze_code(file_path)
            categorized_results = categorize_static_analysis(static_analysis_result)
            llm_summary = llm_static_analysis_summary(static_analysis_result)

            # Combine results with better formatting
            result = f"""Static Analysis Results Summary:\n{llm_summary}\n\n
            Categorized Static Analysis Results:\n
            - Readability Issues:\n{'\n'.join(categorized_results['Readability'])}\n\n
            - Code Quality Issues:\n{'\n'.join(categorized_results['Code Quality'])}\n\n
            - Errors:\n{'\n'.join(categorized_results['Error'])}\n\n
            Full Static Analysis Results:\n{static_analysis_result}
            """

        elif extension in [".txt", ".docx", ".pdf"]:
            # Text file analysis
            text_summary = analyze_text_file(file_path)
            result = f"Text File Analysis Summary:\n{text_summary}"

        else:
            return jsonify({"error": "Unsupported file type for analysis."})

        # Format the JSON response with indentation for readability
        return jsonify({"result": result.replace("\n", "<br>")})  # For browser-friendly newlines

    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"})


if __name__ == "__main__":
    # Initialize the LLaMA-2 model
    initialize_code_interpreter()
    app.run(debug=True)
