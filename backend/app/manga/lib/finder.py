from backend.database.database import collection

class Finder:
    """
    As the class name implies, this is for looking up records in mongo and redis
    """

    @staticmethod
    def search_in_mongo(kwargs):
        # search a record using the title from kwargs
        title = kwargs.get('title')

        if title:
            return collection.find_one({'title': title})

        return None

    @staticmethod
    def search_in_redis(kwargs):
        pass

finder = Finder()