import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("AI_GATEWAY_API_KEY")
GATEWAY_URL = os.environ.get(
    "AI_GATEWAY_URL",
    "https://20.121.19.11:8443/wso2-ai-gateway-demo-usec/clinical-assistant-demo-proxy/chat/completions",
)
PROMPT = os.environ.get("CLINICAL_PROMPT", "Provide a brief daily clinical health tip.")


def run():
    if not API_KEY:
        raise ValueError("AI_GATEWAY_API_KEY environment variable is not set")

    response = requests.post(
        GATEWAY_URL,
        params={"api-version": "2025-01-01-preview"},
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": API_KEY,
        },
        json={
            "messages": [
                {"role": "system", "content": "You are a helpful clinical assistant."},
                {"role": "user", "content": PROMPT},
            ],
            "model": "gpt-4o",
            "max_tokens": 500,
            "temperature": 0.7,
        },
        verify=False,  # gateway uses a self-signed cert
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()
    message = result["choices"][0]["message"]["content"]
    print("Clinical Assistant Response:")
    print(message)


if __name__ == "__main__":
    run()
