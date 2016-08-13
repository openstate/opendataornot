#!/usr/bin/env python
import os
import optparse
import uuid

from flask import (
    Flask, render_template, request, redirect, url_for, send_from_directory)
from werkzeug.utils import secure_filename
from PIL import Image

UPLOAD_FOLDER = '/Users/breyten/sammify/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
MAX_WIDTH = 200
MAX_HEIGHT = 200

def flaskrun(app, default_host="127.0.0.1",
                  default_port="5000"):
    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help="Hostname of the Flask app " + \
                           "[default %s]" % default_host,
                      default=default_host)
    parser.add_option("-P", "--port",
                      help="Port for the Flask app " + \
                           "[default %s]" % default_port,
                      default=default_port)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("-p", "--profile",
                      action="store_true", dest="profile",
                      help=optparse.SUPPRESS_HELP)

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                       restrictions=[30])
        options.debug = True

    app.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_WIDTH'] = MAX_WIDTH
app.config['MAX_HEIGHT'] = MAX_HEIGHT

@app.route("/")
def main():
    return render_template('main.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def process_image(image_file, max_width, max_height):
    image = Image.open(image_file)
    # FIXME: this does not work reliably yet for some reason ...
    image.thumbnail((max_width, max_height), Image.ANTIALIAS)
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
            file_ext = filename.rsplit('.', 1)[1]
            image_file = os.path.join(
                app.config['UPLOAD_FOLDER'],
                u'%s.%s' % (str(uuid.uuid4()), file_ext,))
            file.save(image_file)
            image, pixels = process_image(
                image_file, app.config['MAX_WIDTH'], app.config['MAX_HEIGHT'])
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
    flaskrun(app)
