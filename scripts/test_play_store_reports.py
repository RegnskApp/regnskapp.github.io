import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pprint

PACKAGE_NAME = "com.balancetrackr.app"
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]

# === AUTENTISERING ===
try:
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("androidpublisher", "v3", credentials=credentials)
except Exception as e:
    print("Feil ved autentisering:", e)
    exit(1)

# === HENT RAPPORTER FRA API ===
try:
    response = service.reports().list(
        packageName=PACKAGE_NAME,
        reportType="statistics"
    ).execute()

    if not response or "downloads" not in response:
        print("Ingen rapporter funnet fra API-et.")
    else:
        print(f"{len(response['downloads'])} rapport(er) funnet fra API-et:")
        pprint.pprint(response["downloads"])

except Exception as e:
    print("Feil ved henting av rapporter:", e)
