import requests
import json
from flask import request
from flask_restful import Resource
from backend.database.database import manga_collection
from backend.app.manga.lib.utils import utils
from backend.database.redis import r



class MangaList(Resource):
    """
    Class for searching manga title
    Request would be processed according to this order
    Request -> Redis (Search) -> Mongo (Search) -> Call Mangadex API
    Response -> Store to Mongo -> Send to the client
    """
    base_url = "https://api.mangadex.org"


    def get(self):
        args = request.args
        title = args.get('title')

        if not title:
            return {'msg': 'title not found'}, 404

        # look the title in redis first to avoid processing request in database
        title_in_key_format = utils.transform_to_key_format(title)
        result = r.get(title_in_key_format)

        if not result:
            # look in database
            title_in_pascal_case = utils.transform_to_pascal_case(title)
            record = manga_collection.find({
                'details.attributes.title.en': {'$regex': title_in_pascal_case}
            })

            wrapped_data = {}
        
            if (len(list(record.clone()))):
                wrapped_data = utils.wrapped_response(record, from_db=True)
                r.set(title_in_key_format, json.dumps(wrapped_data))

            else:
                # call the mangadex api to find the manga
                # store the response in db and redis
                response = self._fetch(title)
                _ = self._insert_record(**response)
                wrapped_data = utils.wrapped_response(response, from_db=False)

                r.set(title_in_key_format, json.dumps(wrapped_data))

            if not wrapped_data:
                return {'msg': 'no result found'}, 404

            return wrapped_data, 200

        return json.loads(result), 200

    def _fetch(self, title: str):

        if not title:
            return {'msg': 'title must be indicated.'}, 400

        response = requests.get(
            f"{self.base_url}/manga",
            params={
                'title': title,
                'limit': 20,
            },
        )

        # initial validation in case we didn't receivce any response from the API
        if not response:
            return {}
        
        response = response.json()

        if response['result'] == "error" or response.get('error'):
            return {}  

        return response
    
    @staticmethod 
    def _insert_record(**kwargs):
        data = kwargs.get('data')

        if not data:
            return False
        
        # sample format of the response data from mangadex API
        # {data: [{"id": "", "attributes": {"title": {"en": ""}}}}
        for manga in data:
            title = manga['attributes']['title']['en']

            if manga_collection.find_one({'attributes.title.en': title}):
                continue
            
            manga_collection.insert_one({'details': manga, 'title_key': utils.transform_to_key_format(title)})

        return True