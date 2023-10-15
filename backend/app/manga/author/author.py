from backend.database.redis import r
from backend.app.constants import MANGA_DEX_URL, CACHE_EXPIRY_IN_SECONDS
from backend.database.database import author_colletion
from flask import current_app
import json
import requests


class Author:
    
    def get_author(self, author_id: str):
        redis_key = f"author-{author_id}"
        cached_response = r.get(redis_key)

        if cached_response:
            current_app.logger.info('serving cached response for author')
            return json.loads(cached_response)
        
        document = author_colletion.find_one({'details.id': author_id})

        if document:
            author_name = {'author': document['details']['attributes']['name']}
            r.set(
                redis_key, 
                json.dumps(author_name),
                ex=CACHE_EXPIRY_IN_SECONDS,
            )

        response = requests.get(
            f"{MANGA_DEX_URL}/author/{author_id}"
        )

        if not response:
            return {}

        try:
            response = response.json()
            _ = self._insert_record(response.get('data'))
            author_name = {'author': response.get('data')['attributes']['name']}
            r.set(
                redis_key, 
                json.dumps(author_name),
                ex=CACHE_EXPIRY_IN_SECONDS
            )

            return author_name

        except requests.JSONDecodeError:
            return {}
        
    @staticmethod
    def _insert_record(data: dict):

        if not data:
            return False
        
        if author_colletion.find_one({'details.id': data['id']}):
            return False
        
        author_colletion.insert_one({'details': data})

        return True


author = Author()
