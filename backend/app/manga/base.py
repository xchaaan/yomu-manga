import requests
from flask_restful import Resource
from backend.app.manga.lib.finder import finder

base_url = "https://api.mangadex.org"


class Manga(Resource):
    """
    Base class for fetching API from Mangadex
    Request would be processed according to this order
    Request -> Redis (Search) -> Mongo (Search) -> Call Mangadex API
    Response -> Store to Mongo -> Send to the client
    """

    def get(self, title: str):
        # Todo: Implement looking in redis

        record = finder.search_in_mongo({'title': title})
        
        if not record:
            # call the mangadex api to find the manga
            response = self.fetch(title)

            return response, 200


        return {'msg': 'no result found'}, 404


    def fetch(self, title: str):

        if not title:
            return {'msg': 'title must be indicated.'}, 400

        response = requests.get(
            f"{base_url}/manga",
            params={'title': title},
        )

        # initial validation in case we didn't receivce any response from the API
        if not response:
            return {}
        
        response = response.json()

        if response['result'] == "error" or response.get('error'):
            return {}  

        return response
    
