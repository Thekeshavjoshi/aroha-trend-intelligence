import os
import time

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(api_key=api_key)


# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_NAME = "openai/gpt-oss-120b"

# Keep generated responses controlled.
# Trend detection only needs a compact JSON response.
MAX_OUTPUT_TOKENS = 1800

# Number of retry attempts for temporary rate limits.
MAX_RETRIES = 3


# =========================================================
# LLM RESPONSE
# =========================================================

def generate_response(prompt: str) -> str:
    """
    Send a prompt to Groq and return the generated response.

    Includes:
    - controlled output token usage
    - automatic retry for temporary 429 rate limits
    """

    if not prompt or not prompt.strip():
        return ""

    last_error = None

    for attempt in range(MAX_RETRIES):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2,

                # Prevent unnecessarily long responses.
                max_tokens=MAX_OUTPUT_TOKENS
            )

            return response.choices[0].message.content or ""

        except Exception as error:

            last_error = error

            # -------------------------------------------------
            # Handle Groq rate limits
            # -------------------------------------------------

            if "429" in str(error) or "rate_limit" in str(error).lower():

                if attempt < MAX_RETRIES - 1:

                    wait_time = 3 * (attempt + 1)

                    print(
                        f"\n[Groq Rate Limit] "
                        f"Waiting {wait_time}s before retry "
                        f"({attempt + 1}/{MAX_RETRIES})..."
                    )

                    time.sleep(wait_time)

                    continue

            # -------------------------------------------------
            # Other errors
            # -------------------------------------------------

            raise

    raise last_error

