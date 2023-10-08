from backend.database.database import collection
from bson import ObjectId

class Utils:

    @staticmethod 
    def insert_record(**kwargs):
        data = kwargs.get('data')

        if not data:
            return False
        
        # sample format of the response data from mangadex API
        # {data: [{"id": "", "attributes": {"title": {"en": ""}}}}
        for manga in data:
            title = manga['attributes']['title']['en']

            if collection.find_one({'attributes.title.en': title}):
                continue
            
            _ = collection.insert_one({'details': manga})

        return True


utils = Utils()