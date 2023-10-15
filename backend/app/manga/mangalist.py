import requests
import json
from flask import request, current_app
from flask_restful import Resource
from backend.database.database import manga_collection
from backend.app.manga.lib.utils import utils
from backend.database.redis import r
from backend.app.constants import MANGA_DEX_URL, CACHE_EXPIRY_IN_SECONDS


class MangaList(Resource):
    """
    Class for searching manga title
    Request would be processed according to this order
    Request -> Redis (Search) -> Call MangaDex API
    Response -> Store to Mongo -> Store to redis -> Send to the client
    """
    LIMIT = 20

    def get(self):
        args = request.args
        title = args.get('title')

        if not title:
            return {'msg': 'title not found'}, 404

        # look the title in redis first to avoid processing request in database
        title_in_key_format = utils.transform_to_key_format(title)
        cached_response = r.get(title_in_key_format)

        if not cached_response:
            # call the mangadex api to find the manga
            # store the response in db and redis
            response = self._fetch(title)

            if not response:
                return {'msg': 'no result found'}
            
            _ = self._insert_record(response.get('data'))
            api_response = self._build_api_response(response.get('data'))

            r.set(
                title_in_key_format,
                json.dumps(api_response), 
                ex=CACHE_EXPIRY_IN_SECONDS,
            )

            return api_response, 200

        current_app.logger.info('serving cached response for manga list')
        return json.loads(cached_response), 200

    def _fetch(self, title: str):

        if not title:
            return {'msg': 'title must be indicated.'}, 400

        response = requests.get(
            f"{MANGA_DEX_URL}/manga",
            params={
                'title': title,
                'limit': self.LIMIT,
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
    def _build_api_response(data: dict):

        if not data: 
            return {}

        wrapped_data = {}
        for manga in data:
            title = manga['attributes']['title']['en']
            title_in_key_format = utils.transform_to_key_format(title)
            wrapped_data[title_in_key_format] = {
                "title": title,
                "endpoint": f"/manga/{manga['id']}",
                "id": manga['id']
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
            
            manga_collection.insert_one({'details': manga})

        return True
