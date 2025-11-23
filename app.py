import os
import json
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from pymongo import MongoClient

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Configuration ---
QWEN_API_KEY = os.getenv("AI_ML")
GEMINI_KEY = os.getenv("Gemini_Key")
OPENROUTER_API_KEY = os.getenv("OpenRouter")
GROQ_API_KEY = os.getenv("Groq")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

DB_NAME = "alternate_history"
UNIVERSE_ID = "cold_war_no_moon_landing"

# Initialize Clients
qwen_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=QWEN_API_KEY)
deepseek_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    gemini_model = genai.GenerativeModel("gemini-flash-latest")
else:
    logger.warning("Gemini_Key not found. Model A will fail.")
    gemini_model = None

# --- MongoDB Connection ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
logger.info(f"Connected to MongoDB -> {DB_NAME}")

# --- Create Indexes ---
# Ensure fast lookups by universe_id and sorting by day_index
db.timeline.create_index([("universe_id", 1), ("day_index", -1)])
db.subtopics.create_index([("universe_id", 1), ("day_index", -1)])
db.proposals.create_index([("universe_id", 1), ("day_index", -1)])
db.judgements.create_index([("universe_id", 1), ("day_index", -1)])
logger.info("MongoDB indexes verified.")

# --- Helper Functions ---
def read_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"{filepath} not found.")
        return ""

def clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"): text = text[7:]
    if text.startswith("```"): text = text[3:]
    if text.endswith("```"): text = text[:-3]
    return text.strip()

def extract_json_from_text(text: str) -> str:
    text = clean_json_response(text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        return text[start_idx:end_idx+1]
    return text

def get_next_day_index(universe_id: str) -> int:
    last_subtopic = db.subtopics.find_one({"universe_id": universe_id}, sort=[("day_index", -1)])
    return (last_subtopic["day_index"] + 1) if last_subtopic else 1

def get_recent_events(limit: int = 15) -> str:
    """Fetches and cleans recent timeline events."""
    cursor = db.timeline.find({"universe_id": UNIVERSE_ID}, sort=[("day_index", -1)]).limit(limit)
    events = list(cursor)[::-1]
    cleaned = []
    for e in events:
        e_copy = e.copy()
        for key in ["_id", "created_at", "universe_id"]:
            e_copy.pop(key, None)
        cleaned.append(e_copy)
    return json.dumps(cleaned, indent=2)

def get_previous_subtopics() -> str:
    """Fetches and cleans all previous subtopics."""
    cursor = db.subtopics.find({"universe_id": UNIVERSE_ID}, sort=[("day_index", 1)])
    cleaned = []
    for s in cursor:
        s_copy = s.copy()
        for key in ["_id", "created_at", "universe_id"]:
            s_copy.pop(key, None)
        cleaned.append(s_copy)
    return json.dumps(cleaned, indent=2)

def clean_doc_for_prompt(doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not doc: return {}
    d = doc.copy()
    for key in ["_id", "created_at", "universe_id"]:
        d.pop(key, None)
    return d

def build_prompt(template_path: str, replacements: Dict[str, str]) -> str:
    prompt = read_file(template_path)
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    return prompt

# --- Step 1: Subtopic Generation (Qwen) ---
def generate_subtopic(day_index: int) -> Optional[Dict[str, Any]]:
    logger.info(f"--- Step 1: Generating Subtopic (Qwen) [Day {day_index}] ---")
    
    replacements = {
        "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
        "{{RECENT_TIMELINE_JSON}}": get_recent_events(),
        "{{ALL_PREVIOUS_SUBTOPICS_JSON}}": get_previous_subtopics()
    }
    full_prompt = build_prompt("universe/subtopic_prompt.txt", replacements)
    
    for attempt in range(3):
        try:
            completion = qwen_client.chat.completions.create(
                model="x-ai/grok-4.1-fast:free",
                messages=[{"role": "user", "content": full_prompt}],
                stream=False
            )
            event_data = json.loads(extract_json_from_text(completion.choices[0].message.content))
            
            subtopic_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-subtopic",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "selected_subtopic": event_data.get("selected_subtopic", "Unknown"),
                "reason": event_data.get("reason", ""),
                "tags": event_data.get("expected_focus_tags", []),
                "created_at": datetime.now(timezone.utc)
            }
            db.subtopics.insert_one(subtopic_doc)
            logger.info("Inserted subtopic into MongoDB.")
            return subtopic_doc
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

# --- Step 2: Model A Proposal (Gemini) ---
def generate_model_a_proposal(day_index: int, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info("--- Step 2: Generating Model A Proposal (Gemini) ---")
    if not gemini_model: return None

    replacements = {
        "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
        "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
        "{{RECENT_TIMELINE_JSON}}": get_recent_events()
    }
    full_prompt = build_prompt("universe/model_A_prompt.txt", replacements)
    
    for attempt in range(3):
        try:
            response = gemini_model.generate_content(full_prompt)
            event_data = json.loads(extract_json_from_text(response.text))
            
            proposal_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-A-0",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "model": "A",
                "created_at": datetime.now(timezone.utc),
                **event_data,
                "subtopic": subtopic_data.get("selected_subtopic")
            }
            db.proposals.insert_one(proposal_doc)
            logger.info("Inserted Model A proposal into MongoDB.")
            return proposal_doc
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return None

# --- Step 3: Model B Proposal (DeepSeek) ---
def generate_model_b_proposal(day_index: int, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    logger.info("--- Step 3: Generating Model B Proposal (DeepSeek) ---")
    
    replacements = {
        "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
        "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
        "{{RECENT_TIMELINE_JSON}}": get_recent_events()
    }
    full_prompt = build_prompt("universe/model_B_prompt.txt", replacements)

    try:
        completion = deepseek_client.chat.completions.create(
            extra_headers={"HTTP-Referer": "https://localhost", "X-Title": "Alternate History Engine"},
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": full_prompt}],
            stream=False
        )
        event_data = json.loads(extract_json_from_text(completion.choices[0].message.content))
        
        proposal_doc = {
            "_id": f"{UNIVERSE_ID}-{day_index}-B-0",
            "universe_id": UNIVERSE_ID,
            "day_index": day_index,
            "model": "B",
            "created_at": datetime.now(timezone.utc),
            **event_data,
            "subtopic": subtopic_data.get("selected_subtopic")
        }
        db.proposals.insert_one(proposal_doc)
        logger.info("Inserted Model B proposal into MongoDB.")
        return proposal_doc
    except Exception as e:
        logger.error(f"Error in Step 3: {e}")
        return None

# --- Step 4: Model C Judgment (Groq) ---
def generate_model_c_judgment(day_index: int, subtopic_data: Dict[str, Any], model_a_doc: Optional[Dict[str, Any]], model_b_doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    logger.info("--- Step 4: Generating Model C Judgment (Groq) ---")
    
    replacements = {
        "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
        "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
        "{{RECENT_TIMELINE_JSON}}": get_recent_events(),
        "{{MODEL_A_JSON}}": json.dumps(clean_doc_for_prompt(model_a_doc), indent=2),
        "{{MODEL_B_JSON}}": json.dumps(clean_doc_for_prompt(model_b_doc), indent=2)
    }
    full_prompt = build_prompt("universe/model_C_prompt.txt", replacements)

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
            stream=False
        )
        response_json = json.loads(extract_json_from_text(completion.choices[0].message.content))

        if "accepted_log" in response_json:
            judgment_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-judgment",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "decision": response_json.get("decision", "N/A"),
                "reason": response_json.get("reason", "N/A"),
                "created_at": datetime.now(timezone.utc)
            }
            db.judgements.insert_one(judgment_doc)
            logger.info("Inserted judgment into 'judgements' collection.")

            timeline_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-0",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "subtopic": subtopic_data.get("selected_subtopic"),
                "event": response_json["accepted_log"],
                "created_at": datetime.now(timezone.utc)
            }
            db.timeline.insert_one(timeline_doc)
            logger.info("Inserted accepted event into 'timeline' collection.")
            
            logger.info(f"Decision: {response_json.get('decision', 'N/A')}")
            return timeline_doc
        else:
            logger.error("Error: 'accepted_log' not found in response.")
            return None
    except Exception as e:
        logger.error(f"Error in Step 4: {e}")
        return None

# --- Main Execution ---
def main():
    logger.info("Starting Alternate History Engine Pipeline (MongoDB Version)...")
    
    # Determine Day Index
    day_index = get_next_day_index(UNIVERSE_ID)
    logger.info(f"Processing Day Index: {day_index}")

    # Step 1
    subtopic_doc = generate_subtopic(day_index)
    if not subtopic_doc:
        logger.error("Pipeline stopped at Step 1.")
        return

    # Step 2
    model_a_doc = generate_model_a_proposal(day_index, subtopic_doc)
    if not model_a_doc:
        logger.warning("Pipeline stopped at Step 2 (Model A failed).")
        # Continue to try getting Model B

    # Step 3
    model_b_doc = generate_model_b_proposal(day_index, subtopic_doc)
    if not model_b_doc:
        logger.warning("Pipeline stopped at Step 3 (Model B failed).")

    # Step 4
    if model_a_doc or model_b_doc:
        generate_model_c_judgment(day_index, subtopic_doc, model_a_doc, model_b_doc)
    else:
        logger.error("Both models failed. Cannot proceed to judgment.")

if __name__ == "__main__":
    main()
