from backend.app.constants import MANGA_DEX_URL, CACHE_EXPIRY_IN_SECONDS
from backend.database.redis import r
from backend.database.database import image_collection, chapter_collection
from backend.app.manga.lib.images import images
from flask import current_app
from flask_restful import Resource

import requests
import json


class Chapter(Resource):
    
    def get(self, manga_id: str, chapter_id: str):
        
        if not (manga_id and chapter_id):
            return {'msg': 'url not found'}, 404

        cached_response = r.get(chapter_id)

        # if cached_response:
        #     current_app.logger.info('serving cached response for image url')
        #     return json.loads(cached_response), 200
        
        # look for database record
        document = image_collection.find_one({'_id': chapter_id})

        if document:
            api_response = document['details']
            r.set(
                chapter_id, 
                json.dumps(api_response), 
                ex=CACHE_EXPIRY_IN_SECONDS,
            )

            file_paths = self._get_image_path(api_response, chapter_id)

            return api_response, 200

        api_response = self._fetch(chapter_id)

        if not api_response:
            return {'msg': 'chapter images not found'}, 404
        
        _ = self._insert_record(api_response, chapter_id)
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

    @staticmethod
    def _get_image_path(data: dict, chapter_id: str):
        if not (data and chapter_id):
            return []
        
        document = chapter_collection.find_one({'details.id': chapter_id})
        base_url = data['baseUrl']
        url_hash = data['chapter']['hash']
        file_paths = []
        
        for image_name in data['chapter']['dataSaver']:
            url = f'{base_url}/data-saver/{url_hash}/{image_name}'
            file_path = images.store(**{
                'url': url,
                'title': document['label'],
                'chapter': document['details']['attributes']['chapter']
            })
            break
            if file_path:
                file_paths.append(file_path)

        return file_paths

chapter = Chapter()