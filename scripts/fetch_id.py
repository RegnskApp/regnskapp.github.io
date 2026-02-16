import os
import jwt
import time
import requests

# =========================
# ENVIRONMENT VARIABLES
# =========================
ISSUER_ID = os.environ["ASC_ISSUER_ID"]
KEY_ID = os.environ["ASC_KEY_ID"]
PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")
BUNDLE_ID = "com.olemorten.RegnskApp"

# =========================
# LAG JWT TOKEN
# =========================
def create_token():
    payload = {
        "iss": ISSUER_ID,
        "exp": int(time.time()) + 1200,
        "aud": "appstoreconnect-v1",
    }
    headers = {"kid": KEY_ID}
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="ES256", headers=headers)
    return token

# =========================
# HENT APP UUID
# =========================
def fetch_app_uuid(token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.appstoreconnect.apple.com/v1/apps?filter[bundleId]={BUNDLE_ID}"
    
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    
    if not data.get("data"):
        raise Exception(
            f"Fant ingen app med bundleId '{BUNDLE_ID}'. "
            "Sjekk at API-key og team har tilgang til appen."
        )
    
    app_uuid = data["data"][0]["id"]
    app_name = data["data"][0]["attributes"]["name"]
    print(f"App Name: {app_name}")
    print(f"App UUID: {app_uuid}")
    return app_uuid

# =========================
# MAIN
# =========================
def main():
    token = create_token()
    fetch_app_uuid(token)

if __name__ == "__main__":
    main()
