#!/usr/bin/env python
import os
import optparse
import uuid
from math import floor
import string

from flask import (
    Flask, render_template, request, redirect, url_for, send_from_directory, g)
from werkzeug.utils import secure_filename
from PIL import Image
import sqlite3

DATABASE = '/Users/breyten/sammify/sammify.db'
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

def toBase62(num, b = 62):
    if b <= 0 or b > 62:
        return 0
    base = string.digits + string.lowercase + string.uppercase
    r = num % b
    res = base[r];
    q = floor(num / b)
    while q:
        r = q % b
        q = floor(q / b)
        res = base[int(r)] + res
    return res

def toBase10(num, b = 62):
    base = string.digits + string.lowercase + string.uppercase
    limit = len(num)
    res = 0
    for i in xrange(limit):
        res = b * res + base.find(num[i])
    return res

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def table_check():
    create_table = """
        CREATE TABLE IMAGES (
        ID INTEGER PRIMARY KEY     AUTOINCREMENT,
        FILE  TEXT    NOT NULL
        );
        """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(create_table)
            conn.commit()
        except sqlite3.OperationalError as e:
            print e
            pass

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def main():
    return render_template('main.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def process_image(image_file, max_width, max_height):
    cursor = get_db().cursor()
    insert_row = """
        INSERT INTO IMAGES (FILE)
            VALUES ('%s')
        """ % (image_file,)
    result_cursor = cursor.execute(insert_row)
    get_db().commit()
    encoded_string = toBase62(result_cursor.lastrowid)
    image = Image.open(image_file)
    # FIXME: this does not work reliably yet for some reason ...
    image.thumbnail((max_width, max_height), Image.ANTIALIAS)
    pixels = image.load()
    return encoded_string, image, pixels

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
            encoded_string, image, pixels = process_image(
                image_file, app.config['MAX_WIDTH'], app.config['MAX_HEIGHT'])
            # return render_template(
            #     'upload.html', image=image, pixels=pixels,
            #     image_width=range(image.width),
            #     image_height=range(image.height))
            return redirect(url_for('short_link',
                                    encoded_string=encoded_string))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/i/<encoded_string>')
def short_link(encoded_string):
    image_id = toBase10(encoded_string)
    cursor = get_db().cursor()
    select_row = """
            SELECT FILE FROM IMAGES
                WHERE ID=%s
            """ % (image_id)
    result_cursor = cursor.execute(select_row)
    try:
        image_file = result_cursor.fetchone()[0]
    except Exception as e:
        image_file
    return render_template('short_link.html', image_file=image_file)

if __name__ == "__main__":
    table_check()
    flaskrun(app)
