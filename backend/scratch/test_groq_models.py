import os

import requests
from dotenv import load_dotenv

load_dotenv(".env", override=True)


def test_more_models():
    api_key = os.getenv("GROQ_API_KEY")
    print(f"Testing Groq API key ending in ...{api_key[-4:] if api_key else 'None'}\n")

    candidates = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.2-1b-preview",
        "llama-3.2-3b-preview",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
        "deepseek-r1-distill-qwen-32b",
        "mistral-saba-24b",
        "qwen-2.5-32b",
    ]

    headers = {"Authorization": f"Bearer {api_key}"}

    for model in candidates:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 10,
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        if res.status_code == 200:
            print(
                f"[SUCCESS] {model}: ({res.json()['choices'][0]['message']['content'].strip()})"
            )
        else:
            err_msg = res.json().get("error", {}).get("message", res.text)
            print(f"[FAILED]  {model}: {res.status_code} - {err_msg}")


if __name__ == "__main__":
    test_more_models()
