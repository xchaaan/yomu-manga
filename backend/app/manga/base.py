import requests
from flask_restful import Resource

base_url = "https://api.mangadex.org"


class Manga(Resource):
    """
    Base class for fetching API from Mangadex
    """

    def get(self, title: str):
        return self.search(title)


    def search(self, title: str):

        if not title:
            return {'msg': 'title must be indicated.'}, 400

        response = requests.get(
            f"{base_url}/manga",
            params={'title': title},
        )

        # initial validation in case we didn't receivce empty response from the API
        if not response:
            return {'msg': 'no result found'}, 404
        
        response = response.json()

        # next validation: check the result and data object 
        # sample response: {"result": "ok", "data": {}}

        if response['result'] != "ok" or not response['data']:
            return {'msg': 'no result found'}, 404     

        return response, 200  
