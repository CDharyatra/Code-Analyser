import os
from tkinter import Tk, filedialog, Button, Label, StringVar, Text, Scrollbar
import subprocess

def analyze_code(file_path):
    """
    Analyzes the code file for quality, style, and structure.
    """
    if file_path.endswith(".py"):
        # Use pylint to analyze Python code
        result = subprocess.run(["pylint", file_path], capture_output=True, text=True)
        return result.stdout
    elif file_path.endswith(".js"):
        # Use eslint to analyze JavaScript code (eslint must be installed globally)
        result = subprocess.run(["eslint.cmd", file_path], capture_output=True, text=True)
        return result.stdout
    else:
        return "Unsupported file type for analysis."

def analyze_documentation(file_path):
    if file_path.endswith(".txt"):
        with open(file_path, "r") as file:
            content = file.read()
    elif file_path.endswith(".docx"):
        from docx import Document
        doc = Document(file_path)
        content = " ".join([para.text for para in doc.paragraphs])
    elif file_path.endswith(".pdf"):
        from PyPDF2 import PdfReader
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

def select_and_analyze_file(upload_dir="uploads"):
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = filedialog.askopenfilename(title="Select a File")
    if file_path:
        dest_path = os.path.join(upload_dir, os.path.basename(file_path))
        with open(file_path, "rb") as f:
            with open(dest_path, "wb") as dest:
                dest.write(f.read())

        # Perform analysis
        if file_path.endswith((".py", ".js")):  # Code files
            raw_result = analyze_code(dest_path)
            analysis_result = humanize_analysis(raw_result)
            file_status.set("Analysis Completed")
            # Update the Text widget with the result
            output_text.delete(1.0, "end")  # Clear the previous output
            output_text.insert("end", analysis_result)
        else:
            file_status.set("Unsupported file type.")
            return

        # Save detailed analysis
        report_path = os.path.join(upload_dir, f"{os.path.basename(file_path)}_analysis.txt")
        with open(report_path, "w") as report_file:
            report_file.write(analysis_result)

        print(f"Full analysis saved to: {report_path}")
    else:
        file_status.set("No file selected.")

def humanize_analysis(raw_output):
    """
    Converts raw analysis output into a user-friendly format, with a summary and detailed text.
    """
    # Initialize categories for the summary
    summary = {"Readability": 0, "Descriptions": 0, "Code Quality": 0, "Errors": 0}

    # Process each line of the raw output
    for line in raw_output.splitlines():
        if "line-too-long" in line:
            summary["Readability"] += 1
        elif "missing-module-docstring" in line or "missing-function-docstring" in line:
            summary["Descriptions"] += 1
        elif "subprocess-run-check" in line or "unspecified-encoding" in line or "no-else-return" in line:
            summary["Code Quality"] += 1
        elif "import-error" in line or "global-variable-undefined" in line:
            summary["Errors"] += 1

    # Generate the summary section
    readable_summary = "\nSummary of Issues:\n"
    for category, count in summary.items():
        readable_summary += f"- {category}: {count} issues\n"

    # Append the detailed raw output
    return readable_summary + "\nDetails:\n" + raw_output

def create_gui():
    """
    Creates the GUI for file selection and analysis.
    """
    root = Tk()
    root.title("CodeSentry")
    root.geometry("600x400")  # Initial window size (this will change based on content)

    # Configure window resizing dynamically
    root.grid_columnconfigure(0, weight=1)  # Allow column to expand
    root.grid_rowconfigure(0, weight=0)     # Keep header row fixed size
    root.grid_rowconfigure(1, weight=0)     # Keep the button fixed size
    root.grid_rowconfigure(2, weight=0)     # Keep the status label fixed size
    root.grid_rowconfigure(3, weight=1)     # Allow text box to expand and take remaining space

    # Create the status variable AFTER the root window
    global file_status
    file_status = StringVar()
    file_status.set("No file selected.")

    # Instruction label
    label = Label(root, text="CodeSentry - Clean Code, Neater Docs.", font=("Arial", 32))
    label.grid(row=0, column=0, padx=10, pady=20, sticky="w")

    # Analyze button
    analyze_button = Button(root, text="Select and Analyze File", command=lambda: select_and_analyze_file(), font=("Arial", 12), bg="blue", fg="white")
    analyze_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    # Status label
    status_label = Label(root, textvariable=file_status, font=("Arial", 10), fg="green", wraplength=500, justify="left")
    status_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    # Output Text widget with scrollbar
    global output_text
    output_text = Text(root, height=10, wrap="word", font=("Arial", 12))  # Increased font size here
    output_text.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")  # Expand and take up space

    scrollbar = Scrollbar(root, command=output_text.yview)
    scrollbar.grid(row=3, column=1, sticky="ns")  # Place scrollbar next to Text widget
    output_text.config(yscrollcommand=scrollbar.set)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
