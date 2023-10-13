from flask_restful import Resource
from backend.database.database import manga_collection, chapter_collection
from backend.app.manga.lib.utils import utils
from backend.database.redis import r
from backend.app.global_var import manga_dex_url
from backend.app.manga.author import author
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
        manga_title = document['details']['attributes']['title']['en']
        author_id = document['details']['relationships'][0]['id'] 
        author_name = author.get_author(author_id)
        redis_key = f"manga-{manga_id}-{order}-{str(offset)}"

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

        response = {}

        if not list(chapter_docs.clone()):
            params = {
                'order': order,
                'offset': offset,
            }
            response = self._fetch(manga_id, **params)
 
            if not response:
                return {'msg': f'no available chapter found for {title_key}'}, 404

            _ = self._insert_record(response.get('data'), title_key)      
        
        api_response = self._building_api_response(
            data=response.get('data') if response else chapter_docs, 
            order=order,
            author=author_name,
            title=manga_title,
        )
    
        r.set(redis_key, json.dumps(api_response))
        return api_response, 200
    
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
    def _building_api_response(**kwargs):
        if not kwargs.get('data'):
            return {}
        
        api_response = {}

        for chapter in kwargs.get('data'):
            if chapter.get('details'):
                key = int(chapter['details']['attributes']['chapter'])
                value =  chapter['details']
            else:
                key = api_response[int(chapter['attributes']['chapter'])]
                value = chapter

            api_response[key] = {
                'chapter_id': value['id'],
                'title': kwargs.get('title'),
                'author': kwargs.get('author')['author']
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



        