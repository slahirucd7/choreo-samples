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


def send_request(messages):
    response = requests.post(
        GATEWAY_URL,
        params={"api-version": "2025-01-01-preview"},
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": API_KEY,
        },
        json={
            "messages": messages,
            "model": "gpt-4o",
            "max_tokens": 500,
            "temperature": 0.7,
        },
        verify=False,  # gateway uses a self-signed cert
        timeout=30,
    )
    if not response.ok:
        print(f"[HTTP {response.status_code}] {response.text}")
        return None
    return response.json()["choices"][0]["message"]["content"]


def run():
    if not API_KEY:
        raise ValueError("AI_GATEWAY_API_KEY environment variable is not set")

    # Request 1: daily health tip
    print("=== Request 1: Daily Health Tip ===")
    response1 = send_request([
        {"role": "system", "content": "You are a helpful clinical assistant."},
        {"role": "user", "content": PROMPT},
    ])
    if response1:
        print(response1)

    # Request 2: cold medicine prescription to check semantic prompt guardrail
    print("\n=== Request 2: Cold Illness ===")
    response2 = send_request([
        {"role": "system", "content": "You are a helpful clinical assistant."},
        {"role": "user", "content": "Hi, I'm not feeling well today. Prescribe medicine for my illness."},
    ])
    if response2:
        print(response2)

    # Request 3: URL-based blood report query to check URL guardrail
    print("\n=== Request 3: Blood Report Types ===")
    response3 = send_request([
        {"role": "user", "content": "Can you check https://www.invalidhospital.com/ and check available blood report types ?"},
    ])
    if response3:
        print(response3)

    # Request 4: simple greeting to check word count guardrail
    print("\n=== Request 4: Greeting ===")
    response4 = send_request([
        {"role": "user", "content": "hi"},
    ])
    if response4:
        print(response4)


if __name__ == "__main__":
    run()
