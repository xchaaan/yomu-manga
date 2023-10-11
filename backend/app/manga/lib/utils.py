import re

class Utils:


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