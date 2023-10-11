from flask_restful import Api
from backend.app.manga.mangalist import MangaList
from backend.app.manga.manga import Manga

def create_resources(app):
    api = Api(app)

    api.add_resource(MangaList, '/manga')
    api.add_resource(Manga, '/manga/<string:title_key>')