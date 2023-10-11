from flask_restful import Resource
from backend.database.database import manga_collection, chapter_collection
from backend.app.manga.lib.utils import utils
from backend.app.manga.mangalist import MangaList

import requests


class Manga(Resource):
    """
    Class for giving response containing all the necessary details for the specific manga
    Title, Chapter list and Author
    """

    def get(self, title_key: str):

        if not title_key:
            return {'msg': 'title not found'}, 404

        # get the uuid of this title_key from the database
        document = manga_collection.find_one({'title_key': title_key})

        if not document:
            # we need to invoke the method from mangalist class
            title_query = utils.transform_to_pascal_case(title_key).replace("-", " ")
            response = requests.get(
                url="http://127.0.0.1:5000/manga",
                params={'title': title_query},
                headers={'Content-Type': 'application/json'}
            )
                        
            if response.status_code != 200: 
                return {'msg': 'manga not found'}, 404
            
            print (response.content)
            
        



        