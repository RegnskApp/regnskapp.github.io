import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# === KONFIGURASJON ===
PACKAGE_NAME = "com.balancetrackr.app"  # Din app
OUTPUT_FILE = "data/play_store_history.json"
SCOPES = ['https://www.googleapis.com/auth/androidpublisher']

# === AUTENTISERING MED SERVICE ACCOUNT ===
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('androidpublisher', 'v3', credentials=credentials)

# === HENT TOTAL INSTALLS PER LAND ===
try:
    # Hent user acquisition report for appen
    request = service.reports().get(
        packageName=PACKAGE_NAME,
        reportType='acquisition',  # acquisition = installs
        metrics='installs',
        dimensions='country',
        startDate='2026-01-01',  # dato app ble publisert, eller ønsket start
        endDate='2030-12-31'  # dagens dato eller ønsket end
    )
    response = request.execute()

    by_country = {}
    total_installs = 0

    # response inneholder rader med country + installs
    for row in response.get("rows", []):
        country_code = row.get("country")
        installs = int(row.get("installs", 0))
        by_country[country_code] = installs
        total_installs += installs

except Exception as e:
    print("Feil ved henting av Play Store data:", e)
    by_country = {}
    total_installs = 0

# === LAG JSON OUTPUT ===
daily_data = {
    "total_installs": total_installs,
    "by_country": by_country
}

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w") as f:
    json.dump(daily_data, f, indent=2)

print("Data oppdatert:", daily_data)
