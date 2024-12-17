import ast
import re
from tkinter import Tk, Label, Button, StringVar, Text, Scrollbar, filedialog

def check_coding_standards(code: str):
    warnings = []

    # Basic PEP8 checks
    lines = code.split("\n")
    for i, line in enumerate(lines, start=1):
        if len(line) > 80:
            warnings.append(f"Line {i}: Exceeds 80 characters.")
        if line.endswith(" "):
            warnings.append(f"Line {i}: Trailing whitespace detected.")

    try:
        # AST-based checks
        tree = ast.parse(code)
        class CodeReviewer(ast.NodeVisitor):
            def __init__(self):
                self.warnings = warnings

            def visit_FunctionDef(self, node):
                if len(node.body) > 20:
                    self.warnings.append(f"Function '{node.name}' is too long.")
                if not (isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)):
                    self.warnings.append(f"Function '{node.name}' is missing a docstring.")
                self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    self.warnings.append(f"Avoid using 'print' on line {node.lineno}.")
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name == "*":
                        self.warnings.append(f"Wildcard import '{alias.name}' on line {node.lineno}.")
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module == "*":
                    self.warnings.append(f"Wildcard import from '{node.module}' on line {node.lineno}.")
                self.generic_visit(node)

        reviewer = CodeReviewer()
        reviewer.visit(tree)

    except Exception as e:
        warnings.append(f"Error analyzing code: {e}")

    return warnings

def select_and_analyze_file():
    file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    if not file_path:
        file_status.set("No file selected.")
        return

    try:
        with open(file_path, "r") as file:
            code = file.read()

        file_status.set(f"Analyzing {file_path}...")
        issues = check_coding_standards(code)

        output_text.delete(1.0, "end")
        if issues:
            output_text.insert("end", "\n".join(issues))
        else:
            output_text.insert("end", "No issues found. Great job!")
    except Exception as e:
        file_status.set("Error reading file.")
        output_text.delete(1.0, "end")
        output_text.insert("end", f"An error occurred: {e}")

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
    label = Label(root, text="CodeSentry - Clean Code, Neater Docs.", font=("Arial", 14))
    label.grid(row=0, column=0, padx=10, pady=20, sticky="w")

    # Analyze button
    analyze_button = Button(root, text="Select and Analyze File", command=select_and_analyze_file, font=("Arial", 12), bg="blue", fg="white")
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