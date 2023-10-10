from backend.database.database import collection
import re

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
            
            collection.insert_one({'details': manga})

        return True
    
    @staticmethod
    def transform_to_pascal_case(text: str):
        return text.title()
    
    @staticmethod
    def transform_to_key_format(text: str):
        # remove all special characters from the text and replace space with hyphen
        splitted_char = re.sub('[^a-zA-Z0-9\n \.]', '', text).split()
        return ' '.join(splitted_char).replace(' ', "-").lower()
    
    @staticmethod
    def wrapped_response(data: dict, from_db: bool):
        
        if not data: 
            return {}

        wrapped_data = {}
        collection = data if from_db else data['data']

        for manga in collection:
            
            if from_db:
                title = manga['details']['attributes']['title']['en']
            
            else:
                title = manga['attributes']['title']['en']

            title_in_key_format = utils.transform_to_key_format(title)
            wrapped_data[title_in_key_format] = {
                "title": title,
                "endpoint": f"/{title_in_key_format}"
            }

        return wrapped_data


utils = Utils()