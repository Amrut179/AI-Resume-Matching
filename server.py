from flask import Flask, render_template, request
from src.model import match
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define a route to render the HTML form
@app.route('/')
def index():
    return render_template('index.html')

# Define a route to handle form submission
@app.route('/match', methods=['POST'])
def match_resume():
    resume_files = request.files.getlist('resume')
    job_description = request.form['job_description']
    results = []

    for resume_file in resume_files:
        if resume_file:
            # Save the uploaded file to a specified directory
            resume_filename = secure_filename(resume_file.filename)
            resume_file.save(os.path.join('uploads', resume_filename))

            # Process the resume and job description
            resume_filepath = os.path.join('uploads', resume_filename)
            data = match(resume_filepath, job_description)
            results.append(data)

            # Delete the uploaded file after processing
            os.remove(resume_filepath)
    if results:
        sorted_data = sorted(results, key=lambda x: x["accuracy"], reverse=True)
        return render_template('result.html', data=sorted_data)
    else:
        return "No resume file uploaded."
    
@app.errorhandler(Exception)
def internal_server_error(error):
    return render_template('error.html', error=error)

def main():
    app.run(host='0.0.0.0', port=5000)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)
