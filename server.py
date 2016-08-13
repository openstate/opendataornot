#!/usr/bin/env python

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def main():
    return render_template('main.html')

@app.route("/upload")
def upload():
    return render_template('upload.html')

if __name__ == "__main__":
    app.run()
