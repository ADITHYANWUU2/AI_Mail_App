"""
ai/ai_helper.py — Google Gemini AI Integration with Multi-Key Auto-Failover
==========================================================================
Connects to Google Gemini API (generateContent endpoint).
Maintains a pool of API keys with automatic failover to the next key if quota
or rate limits (429, ResourceExhausted, 403, 400) are encountered on the active key.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Global index tracking the active key in the pool
_CURRENT_KEY_INDEX = 0


def get_api_keys():
    """
    Retrieve all available Gemini API keys as a clean list.
    Supports comma-separated keys in GEMINI_API_KEYS or GEMINI_API_KEY.
    """
    raw_keys = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    return keys


def get_api_key():
    """Get the currently active API key."""
    keys = get_api_keys()
    if not keys:
        return ""
    global _CURRENT_KEY_INDEX
    return keys[_CURRENT_KEY_INDEX % len(keys)]


def rotate_to_next_key():
    """Advance to the next available API key in the pool."""
    global _CURRENT_KEY_INDEX
    keys = get_api_keys()
    if keys:
        _CURRENT_KEY_INDEX = (_CURRENT_KEY_INDEX + 1) % len(keys)
        return keys[_CURRENT_KEY_INDEX]
    return ""


def call_ai(prompt_text, model=None, timeout=45):
    """
    Send a prompt to Google Gemini API and return generated text.
    If quota/tokens/rate-limit are exhausted on one key, automatically
    tries the next key in the pool until success or all keys exhausted.

    Args:
        prompt_text (str): Prompt or instructions for Gemini.
        model (str, optional): Gemini model name (default: 'gemini-1.5-flash').
        timeout (int): Request timeout in seconds.

    Returns:
        str: Generated text response or error message.
    """
    if not prompt_text or not prompt_text.strip():
        return "Error: Prompt cannot be empty."

    keys = get_api_keys()
    if not keys:
        return (
            "Error: No Gemini API keys configured.\n\n"
            "Please add your GEMINI_API_KEYS in the .env file:\n"
            "GEMINI_API_KEYS=key1,key2,key3..."
        )

    model_name = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    total_keys = len(keys)
    last_error = ""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text.strip()}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1024
        }
    }

    # Attempt request across available keys in pool
    global _CURRENT_KEY_INDEX
    for attempt in range(total_keys):
        active_key = keys[_CURRENT_KEY_INDEX % total_keys]
        url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={active_key}"

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                return "No text response received from Gemini."

            # Rate limit, quota exhaustion, or key issue -> rotate to next key
            elif response.status_code in [429, 403, 400]:
                err_text = response.text
                last_error = f"Key #{(_CURRENT_KEY_INDEX % total_keys) + 1} ({active_key[:8]}...) returned status {response.status_code}: {err_text}"
                rotate_to_next_key()
                continue

            else:
                last_error = f"Gemini API Error ({response.status_code}): {response.text}"
                rotate_to_next_key()
                continue

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_error = f"Network error with key #{(_CURRENT_KEY_INDEX % total_keys) + 1}: {str(e)}"
            rotate_to_next_key()
            continue
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            rotate_to_next_key()
            continue

    return f"All {total_keys} Gemini API keys exhausted or rate-limited. Last error: {last_error}"
