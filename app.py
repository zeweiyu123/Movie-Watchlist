import os
from flask import Flask
import certifi
from pymongo import MongoClient
from route import pages

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFw")

    client = MongoClient("mongodb+srv://zeweiyu:YZW20000505@microblog-application.r4fla.mongodb.net/test",tlsCAFile=certifi.where())
    app.db=client.watchlist

    app.register_blueprint(pages)
    return app