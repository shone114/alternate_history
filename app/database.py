from pymongo import MongoClient
from app.config import settings
from app.utils.logging import logger


class Database:
    client: MongoClient = None
    db = None

    def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            logger.info(f"Connected to MongoDB -> {settings.DB_NAME}")
            self._ensure_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
    
    def close(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def _ensure_indexes(self):
        collections = ["timeline", "subtopics", "proposals", "judgements"]
        for col_name in collections:
            self.db[col_name].create_index([("universe_id", 1), ("day_index", -1)])
        logger.info("MongoDB indexes verified.")

    def get_collection(self, name: str):
        return self.db[name]

db = Database()
