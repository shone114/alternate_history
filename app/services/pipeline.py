import json
import time
import pytz
from datetime import datetime
from typing import Optional, Dict, Any

from app.database import db
from app.config import settings
from app.services.llm_service import llm_service
from app.utils.prompts import build_prompt, extract_json_from_text, read_file
from app.utils.logging import logger

class PipelineService:
    def get_next_day_index(self) -> int:
        last_subtopic = db.get_collection("subtopics").find_one(
            {"universe_id": settings.UNIVERSE_ID},
            sort=[("day_index", -1)]
        )
        return (last_subtopic["day_index"] + 1) if last_subtopic else 1

    def get_recent_events(self, limit: int = 15) -> str:
        cursor = db.get_collection("timeline").find(
            {"universe_id": settings.UNIVERSE_ID},
            sort=[("day_index", -1)]
        ).limit(limit)
        events = list(cursor)[::-1]
        cleaned = []
        for e in events:
            e_copy = e.copy()
            for key in ["_id", "created_at", "universe_id"]:
                e_copy.pop(key, None)
            cleaned.append(e_copy)
        return json.dumps(cleaned, indent=2)

    def get_previous_subtopics(self) -> str:
        cursor = db.get_collection("subtopics").find(
            {"universe_id": settings.UNIVERSE_ID},
            sort=[("day_index", 1)]
        )
        cleaned = []
        for s in cursor:
            s_copy = s.copy()
            for key in ["_id", "created_at", "universe_id"]:
                s_copy.pop(key, None)
            cleaned.append(s_copy)
        return json.dumps(cleaned, indent=2)

    def clean_doc_for_prompt(self, doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not doc: return {}
        d = doc.copy()
        for key in ["_id", "created_at", "universe_id"]:
            d.pop(key, None)
        return d

    def generate_subtopic(self, day_index: int) -> Optional[Dict[str, Any]]:
        logger.info(f"--- Step 1: Generating Subtopic [Day {day_index}] ---")
        
        replacements = {
            "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
            "{{RECENT_TIMELINE_JSON}}": self.get_recent_events(),
            "{{ALL_PREVIOUS_SUBTOPICS_JSON}}": self.get_previous_subtopics()
        }
        full_prompt = build_prompt("universe/subtopic_prompt.txt", replacements)
        
        for attempt in range(3):
            try:
                response_text = llm_service.generate_qwen(full_prompt)
                event_data = json.loads(extract_json_from_text(response_text))
                
                subtopic_doc = {
                    "_id": f"{settings.UNIVERSE_ID}-{day_index}-subtopic",
                    "universe_id": settings.UNIVERSE_ID,
                    "day_index": day_index,
                    "selected_subtopic": event_data.get("selected_subtopic", "Unknown"),
                    "reason": event_data.get("reason", ""),
                    "tags": event_data.get("expected_focus_tags", []),
                    "created_at": datetime.now(pytz.timezone("Asia/Kolkata"))
                }
                db.get_collection("subtopics").insert_one(subtopic_doc)
                logger.info("Inserted subtopic into MongoDB.")
                return subtopic_doc
            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        return None

    def generate_model_a(self, day_index: int, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("--- Step 2: Generating Model A Proposal ---")
        
        replacements = {
            "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
            "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
            "{{RECENT_TIMELINE_JSON}}": self.get_recent_events()
        }
        full_prompt = build_prompt("universe/model_A_prompt.txt", replacements)
        
        for attempt in range(3):
            try:
                response_text = llm_service.generate_gemini(full_prompt)
                event_data = json.loads(extract_json_from_text(response_text))
                
                proposal_doc = {
                    "_id": f"{settings.UNIVERSE_ID}-{day_index}-A-0",
                    "universe_id": settings.UNIVERSE_ID,
                    "day_index": day_index,
                    "model": "A",
                    "created_at": datetime.now(pytz.timezone("Asia/Kolkata")),
                    **event_data,
                    "subtopic": subtopic_data.get("selected_subtopic")
                }
                db.get_collection("proposals").insert_one(proposal_doc)
                logger.info("Inserted Model A proposal into MongoDB.")
                return proposal_doc
            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed: {e}")
                time.sleep(2)
        return None

    def generate_model_b(self, day_index: int, subtopic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info("--- Step 3: Generating Model B Proposal ---")
        
        replacements = {
            "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
            "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
            "{{RECENT_TIMELINE_JSON}}": self.get_recent_events()
        }
        full_prompt = build_prompt("universe/model_B_prompt.txt", replacements)

        try:
            response_text = llm_service.generate_deepseek(full_prompt)
            event_data = json.loads(extract_json_from_text(response_text))
            
            proposal_doc = {
                "_id": f"{settings.UNIVERSE_ID}-{day_index}-B-0",
                "universe_id": settings.UNIVERSE_ID,
                "day_index": day_index,
                "model": "B",
                "created_at": datetime.now(pytz.timezone("Asia/Kolkata")),
                **event_data,
                "subtopic": subtopic_data.get("selected_subtopic")
            }
            db.get_collection("proposals").insert_one(proposal_doc)
            logger.info("Inserted Model B proposal into MongoDB.")
            return proposal_doc
        except Exception as e:
            logger.error(f"Error in Step 3: {e}")
            return None

    def generate_model_c(self, day_index: int, subtopic_data: Dict[str, Any], model_a_doc: Optional[Dict[str, Any]], model_b_doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        logger.info("--- Step 4: Generating Model C Judgment ---")
        
        replacements = {
            "{{UNIVERSE_SEED_JSON}}": read_file("universe/universe_seed.json"),
            "{{SUBTOPIC}}": subtopic_data.get("selected_subtopic", ""),
            "{{RECENT_TIMELINE_JSON}}": self.get_recent_events(),
            "{{MODEL_A_JSON}}": json.dumps(self.clean_doc_for_prompt(model_a_doc), indent=2),
            "{{MODEL_B_JSON}}": json.dumps(self.clean_doc_for_prompt(model_b_doc), indent=2)
        }
        full_prompt = build_prompt("universe/model_C_prompt.txt", replacements)

        try:
            response_text = llm_service.generate_groq(full_prompt)
            response_json = json.loads(extract_json_from_text(response_text))

            if "accepted_log" in response_json:
                judgment_doc = {
                    "_id": f"{settings.UNIVERSE_ID}-{day_index}-judgment",
                    "universe_id": settings.UNIVERSE_ID,
                    "day_index": day_index,
                    "decision": response_json.get("decision", "N/A"),
                    "reason": response_json.get("reason", "N/A"),
                    "created_at": datetime.now(pytz.timezone("Asia/Kolkata"))
                }
                db.get_collection("judgements").insert_one(judgment_doc)
                logger.info("Inserted judgment into 'judgements' collection.")

                timeline_doc = {
                    "_id": f"{settings.UNIVERSE_ID}-{day_index}-0",
                    "universe_id": settings.UNIVERSE_ID,
                    "day_index": day_index,
                    "subtopic": subtopic_data.get("selected_subtopic"),
                    "event": response_json["accepted_log"],
                    "created_at": datetime.now(pytz.timezone("Asia/Kolkata"))
                }
                db.get_collection("timeline").insert_one(timeline_doc)
                logger.info("Inserted accepted event into 'timeline' collection.")
                return timeline_doc
            else:
                logger.error("Error: 'accepted_log' not found in response.")
                return None
        except Exception as e:
            logger.error(f"Error in Step 4: {e}")
            return None

    def run_daily_simulation(self) -> Dict[str, Any]:
        day_index = self.get_next_day_index()
        logger.info(f"Starting simulation for Day {day_index}")
        
        subtopic = self.generate_subtopic(day_index)
        if not subtopic: raise Exception("Step 1 Failed")
        
        model_a = self.generate_model_a(day_index, subtopic)
        model_b = self.generate_model_b(day_index, subtopic)
        
        if not model_a and not model_b: raise Exception("Step 2/3 Failed (Both models)")
        
        final_event = self.generate_model_c(day_index, subtopic, model_a, model_b)
        if not final_event: raise Exception("Step 4 Failed")
        
        return {
            "day_index": day_index,
            "subtopic": subtopic,
            "model_a": model_a,
            "model_b": model_b,
            "final_event": final_event
        }

pipeline_service = PipelineService()
