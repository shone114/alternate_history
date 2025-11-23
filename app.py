import os
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from pymongo import MongoClient, ASCENDING

# Load environment variables
load_dotenv()

# --- Configuration ---
QWEN_API_KEY = os.getenv("AI_ML")
GEMINI_KEY = os.getenv("Gemini_Key")
OPENROUTER_API_KEY = os.getenv("OpenRouter")
GROQ_API_KEY = os.getenv("Groq")

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "alternate_history"
UNIVERSE_ID = "cold_war_no_moon_landing"

# Initialize Clients
qwen_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=QWEN_API_KEY,
)

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    gemini_model = genai.GenerativeModel("gemini-flash-latest")
else:
    print("Error: Gemini_Key not found.")
    gemini_model = None

deepseek_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

groq_client = Groq(api_key=GROQ_API_KEY)

# --- MongoDB Connection ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
print(f"Connected to MongoDB -> {DB_NAME}")

# --- Helper Functions ---
def read_file(filepath):
    try:
        with open(filepath, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {filepath} not found.")
        return ""

def clean_json_response(response_text):
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return response_text.strip()

def extract_json_from_text(text):
    text = clean_json_response(text)
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx != -1 and end_idx != -1:
        return text[start_idx:end_idx+1]
    return text

def get_next_day_index(universe_id):
    # Find the max day_index in subtopics
    last_subtopic = db.subtopics.find_one(
        {"universe_id": universe_id},
        sort=[("day_index", -1)]
    )
    if last_subtopic:
        return last_subtopic["day_index"] + 1
    return 1

# --- Step 1: Subtopic Generation (Qwen) ---
def generate_subtopic(day_index):
    print(f"\n--- Step 1: Generating Subtopic (Qwen) [Day {day_index}] ---")
    prompt_text = read_file("universe/subtopic_prompt.txt")
    seed_text = read_file("universe/universe_seed.json")
    
    # Fetch last 15 timeline events
    recent_events_cursor = db.timeline.find(
        {"universe_id": UNIVERSE_ID},
        sort=[("day_index", -1)]
    ).limit(15)
    
    # Convert to list and reverse to get chronological order
    recent_events = list(recent_events_cursor)[::-1]
    
    # Clean up events for prompt
    cleaned_events = []
    for event in recent_events:
        e = event.copy()
        e.pop("_id", None)
        e.pop("created_at", None)
        e.pop("universe_id", None)
        cleaned_events.append(e)
    
    recent_timeline_json = json.dumps(cleaned_events, indent=2)

    # Fetch all previous subtopics
    subtopics_cursor = db.subtopics.find(
        {"universe_id": UNIVERSE_ID},
        sort=[("day_index", 1)]
    )
    
    # Clean up subtopics for prompt
    cleaned_subtopics = []
    for sub in subtopics_cursor:
        s = sub.copy()
        s.pop("_id", None)
        s.pop("created_at", None)
        s.pop("universe_id", None)
        cleaned_subtopics.append(s)
        
    all_previous_subtopics_json = json.dumps(cleaned_subtopics, indent=2)

    # Replace placeholders
    full_prompt = prompt_text.replace("{{UNIVERSE_SEED_JSON}}", seed_text)
    full_prompt = full_prompt.replace("{{RECENT_TIMELINE_JSON}}", recent_timeline_json)
    full_prompt = full_prompt.replace("{{ALL_PREVIOUS_SUBTOPICS_JSON}}", all_previous_subtopics_json)
    
    # Debug: Print start of prompt to verify
    # print(f"DEBUG PROMPT START:\n{full_prompt[:500]}\nDEBUG PROMPT END")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            completion = qwen_client.chat.completions.create(
                model="x-ai/grok-4.1-fast:free",
                messages=[{"role": "user", "content": full_prompt}],
                stream=False
            )
            response_text = completion.choices[0].message.content
            json_text = extract_json_from_text(response_text)
            
            try:
                event_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"Attempt {attempt+1}: JSON Parse Error: {e}")
                print(f"Raw Text: {json_text}")
                raise e

            # Insert into MongoDB
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
            print("Inserted subtopic into MongoDB.")
            
            return subtopic_doc
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                print("Max retries reached for Step 1.")
                return None
            time.sleep(2)

# --- Step 2: Model A Proposal (Gemini) ---
def generate_model_a_proposal(day_index, subtopic_data):
    print("\n--- Step 2: Generating Model A Proposal (Gemini) ---")
    if not gemini_model:
        return None

    prompt_text = read_file("universe/model_A_prompt.txt")
    seed_text = read_file("universe/universe_seed.json")
    
    # Fetch last 15 timeline events
    recent_events_cursor = db.timeline.find(
        {"universe_id": UNIVERSE_ID},
        sort=[("day_index", -1)]
    ).limit(15)
    
    # Convert to list and reverse to get chronological order
    recent_events = list(recent_events_cursor)[::-1]
    
    # Clean up events for prompt
    cleaned_events = []
    for event in recent_events:
        e = event.copy()
        e.pop("_id", None)
        e.pop("created_at", None)
        e.pop("universe_id", None)
        cleaned_events.append(e)
    
    recent_timeline_json = json.dumps(cleaned_events, indent=2)

    # Replace placeholders
    full_prompt = prompt_text.replace("{{UNIVERSE_SEED_JSON}}", seed_text)
    full_prompt = full_prompt.replace("{{SUBTOPIC}}", subtopic_data.get("selected_subtopic", ""))
    full_prompt = full_prompt.replace("{{RECENT_TIMELINE_JSON}}", recent_timeline_json)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = gemini_model.generate_content(full_prompt)
            response_text = response.text
            json_text = extract_json_from_text(response_text)
            event_data = json.loads(json_text)
            
            # Insert into MongoDB
            proposal_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-A-0",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "model": "A",
                "created_at": datetime.now(timezone.utc),
                **event_data # Unpack event data directly
            }
            
            # Ensure subtopic is set correctly if not in event_data or to enforce consistency
            proposal_doc["subtopic"] = subtopic_data.get("selected_subtopic")
            
            db.proposals.insert_one(proposal_doc)
            print("Inserted Model A proposal into MongoDB.")
            
            return proposal_doc
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                print("Max retries reached.")
                return None
            time.sleep(2)

# --- Step 3: Model B Proposal (DeepSeek) ---
def generate_model_b_proposal(day_index, subtopic_data):
    print("\n--- Step 3: Generating Model B Proposal (DeepSeek) ---")
    prompt_text = read_file("universe/model_B_prompt.txt")
    seed_text = read_file("universe/universe_seed.json")
    
    # Fetch last 15 timeline events
    recent_events_cursor = db.timeline.find(
        {"universe_id": UNIVERSE_ID},
        sort=[("day_index", -1)]
    ).limit(15)
    
    # Convert to list and reverse to get chronological order
    recent_events = list(recent_events_cursor)[::-1]
    
    # Clean up events for prompt
    cleaned_events = []
    for event in recent_events:
        e = event.copy()
        e.pop("_id", None)
        e.pop("created_at", None)
        e.pop("universe_id", None)
        cleaned_events.append(e)
    
    recent_timeline_json = json.dumps(cleaned_events, indent=2)

    # Replace placeholders
    full_prompt = prompt_text.replace("{{UNIVERSE_SEED_JSON}}", seed_text)
    full_prompt = full_prompt.replace("{{SUBTOPIC}}", subtopic_data.get("selected_subtopic", ""))
    full_prompt = full_prompt.replace("{{RECENT_TIMELINE_JSON}}", recent_timeline_json)

    try:
        completion = deepseek_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://localhost", 
                "X-Title": "Alternate History Engine", 
            },
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": full_prompt}],
            stream=False
        )
        response_text = completion.choices[0].message.content
        json_text = extract_json_from_text(response_text)
        event_data = json.loads(json_text)
        
        # Insert into MongoDB
        proposal_doc = {
            "_id": f"{UNIVERSE_ID}-{day_index}-B-0",
            "universe_id": UNIVERSE_ID,
            "day_index": day_index,
            "model": "B",
            "created_at": datetime.now(timezone.utc),
            **event_data # Unpack event data directly
        }
        
        # Ensure subtopic is set correctly
        proposal_doc["subtopic"] = subtopic_data.get("selected_subtopic")

        db.proposals.insert_one(proposal_doc)
        print("Inserted Model B proposal into MongoDB.")
        
        return proposal_doc
    except Exception as e:
        print(f"Error in Step 3: {e}")
        return None

# --- Step 4: Model C Judgment (Groq) ---
def generate_model_c_judgment(day_index, subtopic_data, model_a_doc, model_b_doc):
    print("\n--- Step 4: Generating Model C Judgment (Groq) ---")
    prompt_text = read_file("universe/model_C_prompt.txt")
    seed_text = read_file("universe/universe_seed.json")
    
    # Fetch last 15 timeline events
    recent_events_cursor = db.timeline.find(
        {"universe_id": UNIVERSE_ID},
        sort=[("day_index", -1)]
    ).limit(15)
    
    # Convert to list and reverse to get chronological order
    recent_events = list(recent_events_cursor)[::-1]
    
    # Clean up events for prompt
    cleaned_events = []
    for event in recent_events:
        e = event.copy()
        e.pop("_id", None)
        e.pop("created_at", None)
        e.pop("universe_id", None)
        cleaned_events.append(e)
    
    recent_timeline_json = json.dumps(cleaned_events, indent=2)

    # Use passed proposal data. 
    # Note: Since we unpacked the data, we can pass the whole doc or filter.
    # The prompt expects the JSON output. We can just dump the whole doc excluding _id etc if needed,
    # or better, just dump the doc as is, the model can handle extra fields.
    
    def clean_doc_for_prompt(doc):
        if not doc: return {}
        d = doc.copy()
        d.pop("_id", None)
        d.pop("created_at", None)
        d.pop("universe_id", None)
        return d

    log1_str = json.dumps(clean_doc_for_prompt(model_a_doc), indent=2) if model_a_doc else "{}"
    log2_str = json.dumps(clean_doc_for_prompt(model_b_doc), indent=2) if model_b_doc else "{}"

    # Replace placeholders
    full_prompt = prompt_text.replace("{{UNIVERSE_SEED_JSON}}", seed_text)
    full_prompt = full_prompt.replace("{{SUBTOPIC}}", subtopic_data.get("selected_subtopic", ""))
    full_prompt = full_prompt.replace("{{RECENT_TIMELINE_JSON}}", recent_timeline_json)
    full_prompt = full_prompt.replace("{{MODEL_A_JSON}}", log1_str)
    full_prompt = full_prompt.replace("{{MODEL_B_JSON}}", log2_str)

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
            stream=False
        )
        response_text = completion.choices[0].message.content
        json_text = extract_json_from_text(response_text)
        response_json = json.loads(json_text)

        if "accepted_log" in response_json:
            accepted_log = response_json["accepted_log"]
            
            # Insert into Judgements Collection
            judgment_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-judgment",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "decision": response_json.get("decision", "N/A"),
                "reason": response_json.get("reason", "N/A"),
                # Removed raw_output
                "created_at": datetime.now(timezone.utc)
            }
            db.judgements.insert_one(judgment_doc)
            print("Inserted judgment into 'judgements' collection.")

            # Insert into MongoDB (Timeline)
            timeline_doc = {
                "_id": f"{UNIVERSE_ID}-{day_index}-0",
                "universe_id": UNIVERSE_ID,
                "day_index": day_index,
                "subtopic": subtopic_data.get("selected_subtopic"),
                "event": accepted_log,
                "created_at": datetime.now(timezone.utc)
            }
            db.timeline.insert_one(timeline_doc)
            print("Inserted accepted event into 'timeline' collection.")
            
            print(f"Decision: {response_json.get('decision', 'N/A')}")
            print(f"Reason: {response_json.get('reason', 'N/A')}")
            return timeline_doc
        else:
            print("Error: 'accepted_log' not found in response.")
            return None

    except Exception as e:
        print(f"Error in Step 4: {e}")
        return None

# --- Main Execution ---
def main():
    print("Starting Alternate History Engine Pipeline (MongoDB Version)...")
    
    # Determine Day Index
    day_index = get_next_day_index(UNIVERSE_ID)
    print(f"Processing Day Index: {day_index}")

    # Step 1
    subtopic_doc = generate_subtopic(day_index)
    if not subtopic_doc:
        print("Pipeline stopped at Step 1.")
        return

    # Step 2
    model_a_doc = generate_model_a_proposal(day_index, subtopic_doc)
    if not model_a_doc:
        print("Pipeline stopped at Step 2 (Model A failed).")
        # Continue to try getting Model B

    # Step 3
    model_b_doc = generate_model_b_proposal(day_index, subtopic_doc)
    if not model_b_doc:
        print("Pipeline stopped at Step 3 (Model B failed).")

    # Step 4
    if model_a_doc or model_b_doc:
        generate_model_c_judgment(day_index, subtopic_doc, model_a_doc, model_b_doc)
    else:
        print("Both models failed. Cannot proceed to judgment.")

if __name__ == "__main__":
    main()
