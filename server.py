#!/usr/bin/env python
import os

from flask import (
    Flask, render_template, request, redirect, url_for, send_from_directory)
from werkzeug.utils import secure_filename
from PIL import Image

UPLOAD_FOLDER = '/Users/breyten/sammify/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def main():
    return render_template('main.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def process_image(image_file):
    image = Image.open(image_file)
    pixels = image.load()
    return image, pixels

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'picture' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['picture']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_file)
            image, pixels = process_image(image_file)
            return render_template(
                'upload.html', image=image, pixels=pixels,
                image_width=range(image.width),
                image_height=range(image.height))
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run()
