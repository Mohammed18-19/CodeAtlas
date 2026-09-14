import os

from dotenv import load_dotenv
from google import genai

from app.ingestion.rag.prompts import RAGPrompt
from app.ingestion.rag.security import (
    contains_sensitive_output,
    redact_secrets,
    safe_security_response,
)


load_dotenv()


class RAGGenerator:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.prompt_builder = RAGPrompt()

    def generate(
        self,
        question: str,
        context: str,
        history: str = "",
    ) -> str:

        prompt = self.prompt_builder.build(
            question=question,
            context=context,
            history=history,
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        generated_text = redact_secrets(response.text or "")

        if contains_sensitive_output(generated_text):
            return safe_security_response()

        if "[REDACTED]" in generated_text:
            return safe_security_response()

        return generated_text
