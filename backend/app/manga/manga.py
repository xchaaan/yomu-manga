from flask_restful import Resource
from backend.database.database import manga_collection, chapter_collection
from backend.database.redis import r
from backend.app.constants import MANGA_DEX_URL, CACHE_EXPIRY_IN_SECONDS
from backend.app.manga.author.author import author
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
    LIMIT = 500

    def get(self, manga_id: str):

        if not manga_id:
            return {'msg': 'manga not found'}, 404
        
        # accept optional body with keys order and offset
        # offset is use to get the subset of records starting with the given value
        args = request.args
        order = args.get('order', 'asc')
        offset = int(args.get('offset', 0))

        # search for a record from the database using the uuid in query param
        document = manga_collection.find_one({'details.id': manga_id})

        if not document:
            # we need to find the manga using API thru ID
            response = requests.get(f"{MANGA_DEX_URL}/manga/{manga_id}")

            if response.status_code != 200: 
                return {'msg': 'manga not found'}, 404
            
            response_body = response.get('data')
            _ = manga_collection.insert_one({'details': response_body})

        document = document.get('details') if document else response
        manga_title = document['attributes']['title']['en']
        author_id = document['relationships'][0]['id'] 
        author_name = author.get_author(author_id)
        redis_key = f"manga-{manga_id}-{order}-{str(offset)}"

        # look first in the redis if we have cached the response
        cached_response = r.get(redis_key)

        if cached_response:
            current_app.logger.info(f'serving cached response for manga: {manga_id}')
            return json.loads(cached_response), 200

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

        response = {}

        if not list(chapter_docs.clone()):
            params = {
                'order': order,
                'offset': offset,
            }
            response = self._fetch(manga_id, **params)
 
            if not response:
                return {'msg': f'no available chapter found for {manga_title}'}, 404

            _ = self._insert_record(response.get('data'), manga_title)      
        
        api_response = self._build_api_response(
            data=response.get('data') if response else chapter_docs, 
            order=order,
            author=author_name,
            title=manga_title,
            manga_id=manga_id,
        )
    
        r.set(
            redis_key, 
            json.dumps(api_response),
            ex=CACHE_EXPIRY_IN_SECONDS,
        )
        return api_response, 200
    
    def _fetch(self, manga_id: str, **kwargs):
        # send a request to the API
        response = requests.get(
            f"{MANGA_DEX_URL}/manga/{manga_id}/feed",
            params={
                'limit': self.LIMIT,
                'offset': kwargs.get('offset'),
                'order[chapter]': kwargs.get('order'),
                'translatedLanguage[]': 'en',
            }
        )

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
    def _build_api_response(**kwargs):
        if not kwargs.get('data'):
            return {}
        
        api_response = {}

        for chapter in kwargs.get('data'):
            data = chapter.get('details') if chapter.get('details') else chapter
            key = data['attributes']['chapter']
            key = float(key) if not key.isdigit() else int(key)

            # the response body
            api_response[key] = {
                'chapter_id': data['id'],
                'title': kwargs.get('title'),
                'author': kwargs.get('author')['author'],
                'end_point': f'/manga/{kwargs.get("manga_id")}/{data["id"]}'
            }

        # sort the dictionary base on order value 
        return dict(sorted(
            api_response.items(), reverse=kwargs.get('order') == 'desc'
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



        