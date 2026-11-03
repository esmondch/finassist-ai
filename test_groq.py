
import os

import gradio as gr
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Check your .env file."
    )

client = Groq(api_key=api_key)


def ask_groq(message):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are FinAssist AI, a banking customer "
                    "support assistant prototype. Use clear, "
                    "concise language. Do not invent bank policies "
                    "or claim to perform real financial transactions."
                ),
            },
            {"role": "user", "content": message},
        ],
        temperature=0.2,
        max_tokens=400,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    print(ask_groq("Introduce yourself in two sentences."))
