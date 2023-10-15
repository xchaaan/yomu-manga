from flask import current_app
from flask import request
from backend.database.redis import r
from backend.app.constants import CACHE_EXPIRY_IN_SECONDS

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
        
        file_name = url.split("/")[-1]
        path = f'static/{title}/{chapter}'
        file_path = f'{path}/{file_name}'
        
        if not os.path.exists(path):
            os.makedirs(path)

        server_path = f'{request.url_root}static/{title}/{chapter}/{file_name}'

        if os.path.exists(file_path):
            return server_path

        image_data = self._fetch(url)
        
        if not image_data:
            return None

        # store the image in a specified folder
        # /static/{manga_title}/{chapter_number}/image

        with open(file_path, 'wb') as handle:
            current_app.logger.info(f'saving {file_path} into file')
            handle.write(image_data)

        return server_path


    def _fetch(self, url: str):
        response = requests.get(url=url)

        if response.status_code != 200:
            return None
        
        return response.content

images = Images()