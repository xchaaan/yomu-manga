from flask_restful import Resource
from backend.database.database import manga_collection, chapter_collection
from backend.app.manga.lib.utils import utils
from backend.database.redis import r
from backend.app.global_var import manga_dex_url
from flask import current_app
from flask import request

import pymongo
import requests
import json

class Manga(Resource):
    """
    Class for giving response containing all the necessary details for the specific manga
    Title, Chapter list and Author
    """
    LIMIT = 100

    def get(self, title_key: str):

        if not title_key:
            return {'msg': 'title not found'}, 404
        
        # accept optional body with keys order and offset
        # offset is use to get the subset of records starting with the given value
        args = request.args

        order = args.get('order', 'asc')
        offset = int(args.get('offset', 0))

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

        document = manga_collection.find_one({'title_key': title_key})
        manga_id = document['details']['id']
        redis_key = f"{manga_id}-{order}-{str(offset)}" 

        # look first in the redis if we have cached the response
        response = r.get(redis_key)

        if response:
            return json.loads(response), 200

        # we can look into the database. this way we can avoid sending request
        order_type = pymongo.ASCENDING if order == 'asc' else pymongo.DESCENDING
        chapter_docs = chapter_collection.find({
            '$and': [
                {'details.relationships.type': 'manga',},
                {'details.relationships.id': manga_id,},
            ]
        })\
        .limit(self.LIMIT)\
        .sort('details.attributes.chapters', order_type)\
        .skip(offset)

        params = {
            'order': order,
            'offset': offset,
        }

        if not list(chapter_docs.clone()):
            response = self._fetch(manga_id, **params)
 
            if not response:
                return {'msg': f'no available chapter found for {title_key}'}, 404

            _ = self._insert_record(response.get('data'), title_key)      
        
            wrapped_response = self._wrapped_response(response.get('data'), order)
        
        else:
            print ("here")
            wrapped_response = self._wrapped_response(chapter_docs, order)

        r.set(redis_key, json.dumps(wrapped_response))
        return wrapped_response, 200
    
    def _fetch(self, manga_id: str, **kwargs):
        # send a request to the API
        response = requests.get(
            f"{manga_dex_url}/chapter",
            params={
                'manga': manga_id,
                'limit': self.LIMIT,
                'offset': kwargs.get('offset'),
                'order[chapter]': kwargs.get('order'),
                'translatedLanguage[]': 'en',
            }
        )

        print (response.json())

        if not response:
            return {}
        
        try:
            response = response.json()

        except requests.JSONDecodeError:
            current_app.logger.info('unable to decode the response due to empty body')
            return {}
        
        if response['result'] == "error":
            return {}
        
        return response
    
    @staticmethod
    def _wrapped_response(data: dict, order_type: str):
        if not data:
            return {}
        
        wrapped_response = {}

        for chapter in data:
            if chapter.get('details'):
                wrapped_response[int(chapter['details']['attributes']['chapter'])] = chapter['details']
            else:
                wrapped_response[int(chapter['attributes']['chapter'])] = chapter

        # sort the dictionary to asc order  
        return dict(sorted(
            wrapped_response.items(), reverse=order_type=='desc'
        ))

    @staticmethod 
    def _insert_record(data: dict, label: str):
        if not data:
            return False

        for chapter in data:

            if chapter_collection.find_one({'id': chapter['id']}):
                continue
            
            chapter_collection.insert_one({'details': chapter, 'label': label})

        return True            



        