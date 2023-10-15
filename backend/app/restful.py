from flask_restful import Api
from backend.app.manga.mangalist import MangaList
from backend.app.manga.manga import Manga
from backend.app.manga.chapter.chapter import Chapter

def create_resources(app):
    api = Api(app)

    api.add_resource(MangaList, '/manga')
    api.add_resource(Manga, '/manga/<string:manga_id>')
    api.add_resource(Chapter, '/manga/<string:manga_id>/<string:chapter_id>')
