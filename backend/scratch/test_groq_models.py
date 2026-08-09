import os

import requests
from dotenv import load_dotenv

load_dotenv(".env", override=True)


def test_groq_http():
    api_key = os.getenv("GROQ_API_KEY")
    print(
        f"Checking models for GROQ_API_KEY ending in ...{api_key[-4:] if api_key else 'None'}"
    )

    # 1. Fetch available models from Groq API directly via HTTP
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        model_ids = [m["id"] for m in data.get("data", [])]
        print("\nAvailable models for this API key:")
        for m_id in sorted(model_ids):
            print(f"  - {m_id}")
    else:
        print(f"Error fetching models: {resp.status_code} {resp.text}")
        return

    # 2. Test chat completion for candidate models
    print("\nTesting chat completions:")
    for model in sorted(model_ids):
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
                f"[OK] {model}: ({res.json()['choices'][0]['message']['content'].strip()})"
            )
        else:
            err_msg = res.json().get("error", {}).get("message", res.text)
            print(f"[FAILED] {model}: {res.status_code} - {err_msg}")


if __name__ == "__main__":
    test_groq_http()
