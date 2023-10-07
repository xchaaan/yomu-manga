from flask_restful import Api
from backend.app.manga.base import Manga

def create_resources(app):
    api = Api(app)

    api.add_resource(Manga, "/api/v1/manga/<string:title>")