from flask import Flask, request, render_template, jsonify
import os
import subprocess
from docx import Document
from PyPDF2 import PdfReader
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid  # For generating unique identifiers

app = Flask(__name__)
CORS(app)  # Allow all origins for development

UPLOAD_FOLDER = "upload"  # Ensure folder name is correct
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def analyze_code(file_path):
    """
    Analyzes the code file for quality, style, and structure.
    """
    if file_path.endswith(".py"):
        # Use pylint to analyze Python code
        result = subprocess.run(["pylint", file_path], capture_output=True, text=True)
        return result.stdout
    elif file_path.endswith(".js"):
        # Use eslint to analyze JavaScript code
        result = subprocess.run(["eslint.cmd", file_path], capture_output=True, text=True)
        return result.stdout
    elif file_path.endswith(".cpp") or file_path.endswith(".c"):
        # Use cppcheck for C/C++
        result = subprocess.run(["cppcheck", "--enable=all", file_path], capture_output=True, text=True)
        return result.stdout
    elif file_path.endswith(".java"):
        # Use checkstyle for Java
        checkstyle_jar = "path/to/checkstyle.jar"  # Provide the path to your checkstyle JAR
        checkstyle_config = "path/to/sun_checks.xml"  # Provide the path to your checkstyle configuration
        result = subprocess.run(
            ["java", "-jar", checkstyle_jar, "-c", checkstyle_config, file_path],
            capture_output=True,
            text=True
        )
        return result.stdout
    elif file_path.endswith(".html") or file_path.endswith(".css"):
        # Example for HTML/CSS analysis (use tools like tidy or stylelint)
        result = subprocess.run(["tidy", "-errors", "-quiet", file_path], capture_output=True, text=True)
        return result.stdout
    else:
        return "Unsupported file type for analysis."


def analyze_documentation(file_path):
    """
    Analyzes documentation files for keyword usage and clarity.
    """
    if file_path.endswith(".txt"):
        with open(file_path, "r") as file:
            content = file.read()
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        content = " ".join([para.text for para in doc.paragraphs])
    elif file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        content = " ".join([page.extract_text() for page in reader.pages])
    else:
        return "Unsupported documentation format."

    # Basic keyword-based analysis
    keyword_score = sum(1 for keyword in ["introduction", "summary", "methodology"] if keyword.lower() in content.lower())
    clarity_score = len(content.split()) / 100  # Example metric: average word count per section
    return f"Keyword Score: {keyword_score}, Clarity Score: {clarity_score:.2f}"


def generate_report(code_analysis, doc_analysis, output_path):
    report_content = f"""
    Code Analysis:
    {code_analysis}

    Documentation Analysis:
    {doc_analysis}

    Overall Assessment:
    Code Quality: {len(code_analysis.splitlines())} issues
    Documentation Quality: {doc_analysis}

    Final Score: TBD
    """
    with open(output_path, "w") as report:
        report.write(report_content)
    return report_content


def humanize_analysis(raw_output):
    """
    Converts raw analysis output into a user-friendly format, with a summary and detailed text.
    """
    summary = {"Readability": 0, "Descriptions": 0, "Code Quality": 0, "Errors": 0}
    for line in raw_output.splitlines():
        if "line-too-long" in line:
            summary["Readability"] += 1
        elif "missing-module-docstring" in line or "missing-function-docstring" in line:
            summary["Descriptions"] += 1
        elif "subprocess-run-check" in line or "unspecified-encoding" in line or "no-else-return" in line:
            summary["Code Quality"] += 1
        elif "import-error" in line or "global-variable-undefined" in line:
            summary["Errors"] += 1

    readable_summary = "\nSummary of Issues:\n"
    for category, count in summary.items():
        readable_summary += f"- {category}: {count} issues\n"

    return readable_summary + "\nDetails:\n" + raw_output


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    # Create a unique filename to prevent overwriting
    filename = secure_filename(file.filename)
    name, extension = os.path.splitext(filename)
    unique_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}{extension}"

    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)

    if file.filename.endswith((".py", ".js")):
        raw_result = analyze_code(file_path)
        analysis_result = humanize_analysis(raw_result)
        return jsonify({"result": analysis_result})
    elif file.filename.endswith((".txt", ".docx", ".pdf")):
        doc_result = analyze_documentation(file_path)
        return jsonify({"result": doc_result})
    else:
        return jsonify({"error": "Unsupported file type"})


if __name__ == "__main__":
    app.run(debug=True)
