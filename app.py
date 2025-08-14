from flask import Flask, render_template
import os
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    extra_dirs = [
        os.path.join(os.getcwd(), 'templates'),
        os.path.join(os.getcwd(), 'static')
    ]
    extra_files = []
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    extra_files.append(filename)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        extra_files=extra_files  # Força reinício ao alterar HTML/CSS/JS
    )
