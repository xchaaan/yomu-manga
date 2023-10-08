from pymongo import MongoClient

mongo_uri = "mongodb://localhost:27017"
mongo_client = MongoClient(mongo_uri)
db = mongo_client['yomu_manga']
collection = db['manga']