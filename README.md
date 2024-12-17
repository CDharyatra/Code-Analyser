# Code-Anaalyser
CodeSentry is a web-based application built using Flask and HTML. It allows users to upload files and analyze them dynamically. The system provides a clean and responsive user interface, with real-time feedback on file processing and results.<br>
Features
1.	File Upload Functionality<br>
o	Users can upload files using a user-friendly interface.<br>
o	File selection includes a clear button to reset the input.<br>
2.	Dynamic File Analysis<br>
o	Files are processed in the backend using Flask.<br>
o	Results are displayed dynamically using a smooth typing effect.<br>
3.	Modern UI Design<br>
o	Clean, responsive layout with a visually appealing background image.<br>
o	Includes loading animations for real-time feedback.<br>
4.	Error Handling<br>
o	User-friendly messages are displayed for upload errors or backend failures.<br>
<br>

Technology Stack<br>
Backend<br>
•	Python with Flask (lightweight server framework).<br>
Frontend<br>
•	HTML5 and CSS for structure and styling.<br>
•	JavaScript for interactivity (AJAX, loaders, and typing effects).<br>
Assets<br>
•	Static files are stored in the static folder (e.g., background image 18.jpg).<br>
•	Templates, like index.html, are in the templates folder.<br>
<br>
Deployment Instructions <br>
1. Prerequisites<br>
Ensure you have the following installed:<br>
•	Python 3.x<br>
•	Flask<br>
•	PyPDF2<br>
•	Docx<br>
•	Pylint<br>

Running the Application<br>
•	Navigate to the project directory and open Terminal<br>
•	Run the Flask server using the following command : python app.py<br>
•	Open a web browser and go to : http://127.0.0.1:5000<br>

Uploading a File<br>
•	Select a file using the "Upload File" option on the homepage.<br>
•	Click the Upload & Analyse button.<br>
•	Wait for the file to be processed. Results will appear in the "Analysis Result" section.<br>
<br>
Conclusion<br>
CodeSentry is a simple yet effective file upload and analysis tool with a modern design. The backend can be extended to handle more complex file processing tasks, while the frontend provides a clean user experience.


