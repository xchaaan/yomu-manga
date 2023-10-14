from backend.app.constants import MANGA_DEX_URL, CACHE_EXPIRY_IN_SECONDS
from backend.database.redis import r
from backend.database.database import image_collection
from flask import current_app
from flask_restful import Resource

import requests
import json


class Chapter(Resource):
    
    def get(self, manga_id: str, chapter_id: str):
        
        if not (manga_id and chapter_id):
            return {'msg': 'url not found'}, 404

        cached_response = r.get(chapter_id)

        if cached_response:
            current_app.logger.info('serving cached response for image url')
            return json.loads(cached_response), 200
        
        # look for database record
        document = image_collection.find_one({'_id': chapter_id})

        if document:
            api_response = document['details']
            r.set(
                chapter_id, 
                json.dumps(api_response), 
                ex=CACHE_EXPIRY_IN_SECONDS,
            )

            return api_response, 200

        api_response = self._fetch(chapter_id)

        if not api_response:
            return {'msg': 'chapter images not found'}, 404
        
        _ = self._insert_record(api_response.get('chapter'), chapter_id)
        r.set(
            chapter_id, 
            json.dumps(api_response.get('chapter')),
            ex=CACHE_EXPIRY_IN_SECONDS
        )
        
        return api_response.get('chapter'), 200

    def _fetch(self, chapter_id: str):
        response = requests.get(
            f'{MANGA_DEX_URL}/at-home/server/{chapter_id}'
        )

        print(response.status_code)
        if not response:
            return {}
        
        try:
            response = response.json()

        except requests.JSONDecodeError:
            return {}
        
        return response


    @staticmethod
    def _insert_record(data: dict, chapter_id: str):
        
        if image_collection.find_one({'_id': chapter_id}):
            return False
        
        image_collection.insert_one({'_id': chapter_id, 'details': data})

        return True


chapter = Chapter()