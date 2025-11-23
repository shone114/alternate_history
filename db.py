import json
from datetime import datetime
from pymongo import MongoClient, ASCENDING

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "alternate_history"

UNIVERSE_ID = "cold_war_no_moon_landing"
UNIVERSE_SEED_PATH = "universe/universe_seed.json"   # make sure this file exists


# -------------------------------------------------------
# CONNECT TO MONGO
# -------------------------------------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

print(f"Connected to MongoDB → {DB_NAME}")


# -------------------------------------------------------
# CREATE COLLECTIONS (Mongo creates automatically on insert,
# but we want to ensure indexes & structure set up now)
# -------------------------------------------------------

collections = [
    "universe",
    "subtopics",
    "proposals",
    "judgements",
    "timeline"
]

for col in collections:
    if col not in db.list_collection_names():
        db.create_collection(col)
        print(f"Created collection: {col}")
    else:
        print(f"Collection already exists: {col}")


# -------------------------------------------------------
# ADD INDEXES
# -------------------------------------------------------

# Indexes for quick queries by universe_id + day_index
db.subtopics.create_index([("universe_id", ASCENDING), ("day_index", ASCENDING)])
db.proposals.create_index([("universe_id", ASCENDING), ("day_index", ASCENDING)])
db.judgements.create_index([("universe_id", ASCENDING), ("day_index", ASCENDING)])
db.timeline.create_index([("universe_id", ASCENDING), ("day_index", ASCENDING)])

# NOTE: Do NOT attempt to create an index on _id (MongoDB enforces this automatically).
# If you want a unique field other than _id, create an index on that field:
# db.universe.create_index([("slug", ASCENDING)], unique=True)

print("Indexes created successfully.")


# -------------------------------------------------------
# LOAD UNIVERSE SEED
# -------------------------------------------------------
try:
    with open(UNIVERSE_SEED_PATH, "r", encoding="utf-8") as f:
        seed_json = json.load(f)
except FileNotFoundError:
    print(f"ERROR: universe_seed.json not found at: {UNIVERSE_SEED_PATH}")
    exit(1)

# Insert seed document if not already present
if db.universe.find_one({"_id": UNIVERSE_ID}):
    print("Universe already exists, skipping insert.")
else:
    db.universe.insert_one({
        "_id": UNIVERSE_ID,
        "title": "Cold War Without The Apollo 11 Moon Landing",
        "universe_seed": seed_json,
        "created_at": datetime.utcnow()
    })
    print("Inserted universe seed into 'universe' collection.")


print("Database initialization complete.")
