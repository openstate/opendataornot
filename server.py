#!/usr/bin/env python

from flask import Flask
app = Flask(__name__)

@app.route("/")
def main():
    return "Hello World!"

@app.route("/upload")
def upload():
    return "upload a file here!"

if __name__ == "__main__":
    app.run()
