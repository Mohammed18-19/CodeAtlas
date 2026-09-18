import os

from dotenv import load_dotenv
from openai import OpenAI

from app.ingestion.rag.prompts import RAGPrompt
from app.ingestion.rag.security import (
    contains_sensitive_output,
    redact_secrets,
    safe_security_response,
)


load_dotenv()


class RAGGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
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

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        generated_text = redact_secrets(
            response.choices[0].message.content or ""
        )

        if contains_sensitive_output(generated_text):
            return safe_security_response()

        if "[REDACTED]" in generated_text:
            return safe_security_response()

        return generated_text