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


utils = Utils()