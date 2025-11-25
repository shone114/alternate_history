from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import settings
from app.utils.logging import logger


class Database:
    client: MongoClient = None
    db = None

    def connect(self):
        try:
            # Enhanced connection configuration for MongoDB Atlas compatibility
            connection_params = {
                'serverSelectionTimeoutMS': 5000,  # 5 second timeout
                'connectTimeoutMS': 10000,  # 10 second connection timeout
                'socketTimeoutMS': 45000,  # 45 second socket timeout
                'maxPoolSize': 50,  # Connection pool size
                'retryWrites': True,  # Retry writes on network errors
            }
            
            # Add TLS/SSL for Atlas connections (mongodb+srv:// automatically uses TLS)
            if settings.MONGO_URI.startswith('mongodb+srv://'):
                connection_params['tls'] = True
                connection_params['tlsAllowInvalidCertificates'] = False
            
            self.client = MongoClient(settings.MONGO_URI, **connection_params)
            
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[settings.DB_NAME]
            logger.info(f"Connected to MongoDB -> {settings.DB_NAME}")
            self._ensure_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error("Please check your MONGO_URI in .env file")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
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
