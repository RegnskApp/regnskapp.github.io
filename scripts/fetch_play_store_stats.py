import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# === KONFIGURASJON ===
PACKAGE_NAME = "com.balancetrackr.app"  # <-- Endre til din app
OUTPUT_FILE = "data/play_store_history.json"
SCOPES = ['https://www.googleapis.com/auth/androidpublisher']

# === AUTENTISERING MED SERVICE ACCOUNT ===
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('androidpublisher', 'v3', credentials=credentials)

# === HENT DAGENS INSTALL/SALES DATA ===
# Play Developer API gir ikke direkte "total installs", men gir kjøp/install events
# Vi kan hente financial reports eller purchases.products.list per SKU
# Her henter vi alle produkter og summerer antall kjøp/install
# OBS: Du må ha riktig SKU og produkt opprettet i Play Console

today = datetime.utcnow().strftime("%Y-%m-%d")

# Eksempel: hent purchases for produktene (for alle brukere)
# Merk: hvis du ikke selger produkter i app, må du bruke install-statistikk via financial reports
# Her gjør vi en placeholder-metode som viser hvordan data hentes

daily_data = {
    "date": today,
    "package_name": PACKAGE_NAME,
    "daily_installs": 0,
    "purchases": []
}

# Prøv å hente kjøp av produkter (alle SKU-er)
try:
    # Hent alle purchases for appen
    request = service.purchases().products().list(packageName=PACKAGE_NAME)
    response = request.execute()

    # Summer alle purchases/install events
    purchases = response.get("purchases", [])
    daily_data["daily_installs"] = len(purchases)
    daily_data["purchases"] = purchases

except Exception as e:
    print("Feil ved henting av Play Store data:", e)

# === LAG JSON OUTPUT ===
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
if os.path.exists(OUTPUT_FILE):
    # Les tidligere data og legg til ny dag
    with open(OUTPUT_FILE, "r") as f:
        history = json.load(f)
else:
    history = []

history.append(daily_data)

with open(OUTPUT_FILE, "w") as f:
    json.dump(history, f, indent=2)

print("Data oppdatert:", daily_data)
