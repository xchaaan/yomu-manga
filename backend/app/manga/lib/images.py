from flask import current_app

import requests
import os

class Images:
    """
    Images: Class for storing compressed images in file system
    """

    def store(self, **kwargs):
        title = kwargs.get('title')
        chapter = kwargs.get('chapter')
        url = kwargs.get('url')

        if not (title and chapter and url):
            return None
        
        path = f'../static/{title}/{chapter}'
        file_name = url.split("/")[-1]
        file_path = f'{path}/{file_name}'
        
        if not os.path.exists(path):
            os.makedirs(path)

        # check if file was already save.
        if os.path.exists(file_path):
            return file_path

        image_data = self._fetch(url)
        
        if not image_data:
            return None

        # store the image in a specified folder
        # /static/{manga_title}/{chapter_number}/image
        print (image_data)

        # with open(file_path, 'wb') as handle:
        #     current_app.logger.info(f'saving {file_path} into file system')
            # handle.write(image_data)

        return file_path

    def _fetch(self, url: str):
        response = requests.get(url=url)

        if response.status_code != 200:
            return None
        
        return response.content

images = Images()