from flask import Flask
from backend.app.app import Application

server = Flask(__name__)
app = Application(server)
app.setup()

@server.route('/')
def index():
    return "<h1>Hello, I am Yomu! </h1>"
