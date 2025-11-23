from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from app.config import settings
from app.utils.logging import logger

class LLMService:
    def __init__(self):
        self.qwen_client = OpenAI(
            base_url="https://openrouter.ai/api/v1", 
            api_key=settings.QWEN_API_KEY or "dummy-key"
        )
        self.deepseek_client = OpenAI(
            base_url="https://openrouter.ai/api/v1", 
            api_key=settings.OPENROUTER_API_KEY or "dummy-key"
        )
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY or "dummy-key")
        
        if settings.GEMINI_KEY:
            genai.configure(api_key=settings.GEMINI_KEY)
            self.gemini_model = genai.GenerativeModel("gemini-flash-latest")
        else:
            logger.warning("Gemini Key missing. Model A will fail.")
            self.gemini_model = None

    def generate_qwen(self, prompt: str) -> str:
        completion = self.qwen_client.chat.completions.create(
            model="x-ai/grok-4.1-fast:free",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return completion.choices[0].message.content

    def generate_gemini(self, prompt: str) -> str:
        if not self.gemini_model:
            raise ValueError("Gemini model not configured")
        response = self.gemini_model.generate_content(prompt)
        return response.text

    def generate_deepseek(self, prompt: str) -> str:
        completion = self.deepseek_client.chat.completions.create(
            extra_headers={"HTTP-Referer": "https://localhost", "X-Title": "Alternate History Engine"},
            model="tngtech/deepseek-r1t-chimera:free",
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return completion.choices[0].message.content

    def generate_groq(self, prompt: str) -> str:
        completion = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            stream=False
        )
        return completion.choices[0].message.content

llm_service = LLMService()
