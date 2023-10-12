import requests
import json
from flask import request, current_app
from flask_restful import Resource
from backend.database.database import manga_collection
from backend.app.manga.lib.utils import utils
from backend.database.redis import r
from backend.app.global_var import manga_dex_url



class MangaList(Resource):
    """
    Class for searching manga title
    Request would be processed according to this order
    Request -> Redis (Search) -> Call MangaDex API
    Response -> Store to Mongo -> Store to redis -> Send to the client
    """

    def get(self):
        args = request.args
        title = args.get('title')

        if not title:
            return {'msg': 'title not found'}, 404

        # look the title in redis first to avoid processing request in database
        title_in_key_format = utils.transform_to_key_format(title)
        result = r.get(title_in_key_format)

        if not result:
            # call the mangadex api to find the manga
            # store the response in db and redis
            response = self._fetch(title)

            if not response:
                return {'msg': 'no result found'}
            
            _ = self._insert_record(response.get('data'))
            wrapped_data = self.wrapped_response(response.get('data'))

            r.set(title_in_key_format, json.dumps(wrapped_data))

            return wrapped_data, 200

        return json.loads(result), 200

    def _fetch(self, title: str):

        if not title:
            return {'msg': 'title must be indicated.'}, 400

        response = requests.get(
            f"{manga_dex_url}/manga",
            params={
                'title': title,
                'limit': 20,
            },
        )

        # initial validation in case we didn't receivce any response from the API
        if not response:
            return {}
        
        try:
            response = response.json()

        except requests.JSONDecodeError:
            current_app.logger.info('unable to decode response due to empty body')
            return {}
        
        if response['result'] == "error":
            return {}

        return response
    
    @staticmethod
    def wrapped_response(data: dict):

        if not data: 
            return {}

        wrapped_data = {}
        for manga in data:
            title = manga['attributes']['title']['en']

            title_in_key_format = utils.transform_to_key_format(title)
            wrapped_data[title_in_key_format] = {
                "title": title,
                "endpoint": f"/{title_in_key_format}"
            }

        return wrapped_data

    @staticmethod 
    def _insert_record(data: dict):

        if not data:
            return False
        
        # sample format of the response data from mangadex API
        # {data: [{"id": "", "attributes": {"title": {"en": ""}}}}
        for manga in data:
            title = manga['attributes']['title']['en']

            if manga_collection.find_one({'details.id': manga['id']}):
                continue
            
            manga_collection.insert_one({'details': manga, 'title_key': utils.transform_to_key_format(title)})

        return True