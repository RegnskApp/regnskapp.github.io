import os
import time
import jwt
import requests

# ===== KONFIG =====
BUNDLE_ID = "com.ole.balancetrackr"  # Din app bundle ID

ASC_ISSUER_ID = os.environ["ASC_ISSUER_ID"]
ASC_KEY_ID = os.environ["ASC_KEY_ID"]
ASC_PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")

# ===== LAG JWT =====
def create_token():
    now = int(time.time())
    payload = {
        "iss": ASC_ISSUER_ID,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1"
    }
    headers = {"alg": "ES256", "kid": ASC_KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, ASC_PRIVATE_KEY, algorithm="ES256", headers=headers)

# ===== HENT APP UUID FRA BUNDLE ID =====
def fetch_app_uuid(token):
    url = f"https://api.appstoreconnect.apple.com/v1/apps?filter[bundleId]={BUNDLE_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    app_uuid = data["data"][0]["id"]
    return app_uuid

# ===== MAIN =====
def main():
    token = create_token()
    app_uuid = fetch_app_uuid(token)
    print(f"App UUID for bundle '{BUNDLE_ID}' er: {app_uuid}")

if __name__ == "__main__":
    main()
