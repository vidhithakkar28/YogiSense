from flask import Flask, render_template, send_from_directory
import os
import subprocess

app = Flask(__name__, template_folder='templates')

# Serve the homepage
@app.route('/')
def home():
    return render_template('index.html')  # index.html is inside templates/

# Serve static files from templates/ folder (your non-standard structure)
@app.route('/<path:filename>')
def serve_static_from_templates(filename):
    return send_from_directory(os.path.join(app.root_path, 'templates'), filename)

# Run the main.py script when clicking ⇒
@app.route('/run-main')
def run_main():
    try:
        subprocess.Popen(['python', 'main.py'])
        return "Yoga pose detection started!"
    except Exception as e:
        return f"Failed to run main.py: {e}"

if __name__ == '__main__':
    app.run(debug=True)
