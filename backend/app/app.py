from backend.app import restful
from backend.database import database

class Application:

    def __init__(self, server) -> None:
        self.restful = restful
        self.server = server

    def setup(self):
        self.restful.create_resources(self.server)