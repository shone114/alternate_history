from typing import Dict
from app.utils.logging import logger

def read_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"{filepath} not found.")
        return ""

def build_prompt(template_path: str, replacements: Dict[str, str]) -> str:
    prompt = read_file(template_path)
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)
    return prompt

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
