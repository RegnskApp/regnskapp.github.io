import os
from google.cloud import storage
import json

# === KONFIGURASJON ===
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = "playstore-reports"  # <-- endre til din bucket
PREFIX = "earnings/"  # eller "statistics/" avhengig av rapporttype

# === INITIER STORAGE CLIENT ===
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
bucket = client.bucket(BUCKET_NAME)

# === LIST FILER I BUCKET ===
blobs = list(bucket.list_blobs(prefix=PREFIX))
if not blobs:
    print("Ingen rapporter funnet i bucket.")
else:
    print(f"{len(blobs)} rapport(er) funnet:")
    for blob in blobs:
        print(f"- {blob.name}")

# === LAST NED EN RAPPORT (eksempel: siste fil) ===
if blobs:
    latest_blob = sorted(blobs, key=lambda b: b.name, reverse=True)[0]
    content = latest_blob.download_as_bytes()
    print(f"\nInnhold fra {latest_blob.name} (første 500 byte):")
    print(content[:500])
