import requests
from config import Config
import sys


def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(Config.CONSUMER_KEY, Config.CONSUMER_SECRET))
    return response.json().get('access_token')


def register_urls(your_domain):
    token = get_access_token()
    if not token:
        print("❌ Failed to get access token. Check your CONSUMER_KEY and CONSUMER_SECRET")
        return

    url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "ShortCode": Config.BUSINESS_SHORTCODE,
        "ResponseType": "Completed",
        "ConfirmationURL": f"{your_domain}/confirmation",
        "ValidationURL": f"{your_domain}/validation"
    }

    print(f"📡 Registering URLs for shortcode: {Config.BUSINESS_SHORTCODE}")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ URLs registered successfully!")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   {response.text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python register_daraja.py https://your-domain.com")
        sys.exit(1)
    register_urls(sys.argv[1].rstrip('/'))