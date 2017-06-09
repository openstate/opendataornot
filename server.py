#!/usr/bin/env python
import os
import optparse
import uuid

from flask import (
    Flask, render_template, request, redirect, url_for, g,
    flash)
import magic
import requests
from werkzeug.utils import secure_filename
import sqlite3
import json

DATABASE = '/opt/opendataornot/sammify.db'
UPLOAD_FOLDER = '/opt/opendataornot/uploads'


def flaskrun(app, default_host="0.0.0.0", default_port="5000"):
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
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        options.debug = True

    app.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )

app = Flask(__name__)
app.secret_key = 'r\xfcp\xca(_\x06\x12\x8d\x91\xc7\x12u\x98\x15_\xed\x82\n%'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMPLATES_AUTO_RELOAD'] = True


class BaseFileParser(object):
    def __init__(self, local_file, local_file_extension, mime_type):
        self.local_file = local_file
        self.local_file_extension = local_file_extension
        self.mime_type = mime_type

    def get_stars(self):
        return 1

    def get_rights(self):
        return None


class PDFOrExcelParser(BaseFileParser):
    def get_stars(self):
        if self.local_file_extension in ['pdf', 'xls', 'xlsx', 'xlsm']:
            return 2
        if self.local_file_extension in ['pdf']:
            return 1
        return 0


class JSONOrCSVParser(BaseFileParser):
    def get_stars(self):
        if self.local_file_extension in ['json', 'csv', 'tsv']:
            return 3
        return 0


class XMLParser(BaseFileParser):
    def get_stars(self):
        if self.local_file_extension in ['xml']:
            return 4
        return 0


class RDFParser(BaseFileParser):
    def get_stars(self):
        if self.local_file_extension in ['rdf']:
            return 5
        return 0


PARSER_CLASSES = [
    BaseFileParser, PDFOrExcelParser, XMLParser, RDFParser]


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


def download_file(url):
    local_filename = url.split('/')[-1]

    try:
        file_ext = local_filename.rsplit('.', 1)[1]
    except LookupError:
        file_ext = 'html'

    image_file = os.path.join(
        app.config['UPLOAD_FOLDER'],
        u'%s.%s' % (str(uuid.uuid4()), file_ext,))

    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)

    if r.status_code < 200 or r.status_code >= 300:
        return None

    with open(image_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                # f.flush() commented by recommendation from J.F.Sebastian
    return image_file, file_ext


def process_link(link):
    local_file, local_ext = download_file(link)
    return process_local_file(local_file, local_ext)


def process_local_file(local_file, local_ext):
    m = magic.Magic(mime=True, uncompress=True)
    result = m.from_file(local_file)

    stars = []
    rights = []
    for parser in PARSER_CLASSES:
        p = parser(local_file, local_ext, result)
        stars.append(p.get_stars())
        rights.append(p.get_rights())
    num_stars = max(stars)
    known_rights = [r for r in rights if r is not None]

    licenses = []
    with open('data/licenses.json', 'r') as in_file:
        licenses = json.load(in_file)

    return render_template(
        'upload.html', mime_type=result, file_name=local_file,
        file_extension=local_ext, stars=num_stars, rights=known_rights,
        licenses=licenses)


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def main():
    return render_template('main.html')


def allowed_file(filename):
    return True


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'picture' not in request.files:
            return process_link(request.form['link'])

        file = request.files['picture']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return process_link(request.form['link'])
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1]
            image_file = os.path.join(
                app.config['UPLOAD_FOLDER'],
                u'%s.%s' % (str(uuid.uuid4()), file_ext,))
            file.save(image_file)
            return process_local_file(image_file, file_ext)
    return render_template('upload.html')

if __name__ == "__main__":
    table_check()
    flaskrun(app)
