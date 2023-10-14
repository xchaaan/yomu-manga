from backend.database.redis import r
from backend.app.global_var import manga_dex_url
from backend.database.database import author_colletion
from flask import current_app
import json
import requests


class Author:
    
    def get_author(self, author_id: str):
        redis_key = f"author-{author_id}"
        response = r.get(redis_key)

        if response:
            current_app.logger.info('serving cached response for author')
            return json.loads(response)
        
        document = author_colletion.find_one({'details.id': author_id})

        if document:
            author_name = {'author': document['details']['attributes']['name']}
            r.set(redis_key, json.dumps(author_name))

        response = requests.get(
            f"{manga_dex_url}/author/{author_id}"
        )

        if not response:
            return {}

        try:
            response = response.json()
            _ = self._insert_record(response.get('data'))
            author_name = {'author': response.get('data')['attributes']['name']}
            r.set(redis_key, json.dumps(author_name))

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