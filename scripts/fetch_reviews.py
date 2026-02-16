import os
import json
import time
import requests
import jwt
from collections import defaultdict

# ========= KONFIG =========
APP_ID = "6743946348"
HISTORY_FILE = "data/asc_reviews.json"

ASC_ISSUER_ID = os.environ["ASC_ISSUER_ID"]
ASC_KEY_ID = os.environ["ASC_KEY_ID"]
ASC_PRIVATE_KEY = os.environ["ASC_PRIVATE_KEY"].replace("\\n", "\n")

# ========= LANDKODER TIL NAVN =========
COUNTRY_NAMES = {
    "ABW": "Aruba", "AFG": "Afghanistan", "AGO": "Angola", "AIA": "Anguilla",
    "ALB": "Albania", "AND": "Andorra", "ANT": "Netherlands Antilles", "ARE": "United Arab Emirates",
    "ARG": "Argentina", "ARM": "Armenia", "ASM": "American Samoa", "ATG": "Antigua and Barbuda",
    "AUS": "Australia", "AUT": "Austria", "AZE": "Azerbaijan", "BDI": "Burundi",
    "BEL": "Belgium", "BEN": "Benin", "BES": "Bonaire, Sint Eustatius and Saba", "BFA": "Burkina Faso",
    "BGD": "Bangladesh", "BGR": "Bulgaria", "BHR": "Bahrain", "BHS": "Bahamas",
    "BIH": "Bosnia and Herzegovina", "BLR": "Belarus", "BLZ": "Belize", "BMU": "Bermuda",
    "BOL": "Bolivia", "BRA": "Brazil", "BRB": "Barbados", "BRN": "Brunei",
    "BTN": "Bhutan", "BWA": "Botswana", "CAF": "Central African Republic", "CAN": "Canada",
    "CHE": "Switzerland", "CHL": "Chile", "CHN": "China", "CIV": "Ivory Coast", "CMR": "Cameroon",
    "COD": "Democratic Republic of the Congo", "COG": "Republic of the Congo", "COK": "Cook Islands",
    "COL": "Colombia", "COM": "Comoros", "CPV": "Cape Verde", "CRI": "Costa Rica",
    "CUB": "Cuba", "CUW": "Curacao", "CXR": "Christmas Island", "CYM": "Cayman Islands",
    "CYP": "Cyprus", "CZE": "Czech Republic", "DEU": "Germany", "DJI": "Djibouti",
    "DMA": "Dominica", "DNK": "Denmark", "DOM": "Dominican Republic", "DZA": "Algeria",
    "ECU": "Ecuador", "EGY": "Egypt", "ERI": "Eritrea", "ESP": "Spain",
    "EST": "Estonia", "ETH": "Ethiopia", "FIN": "Finland", "FJI": "Fiji", "FLK": "Falkland Islands",
    "FRA": "France", "FRO": "Faroe Islands", "FSM": "Micronesia", "GAB": "Gabon",
    "GBR": "United Kingdom", "GEO": "Georgia", "GGY": "Guernsey", "GHA": "Ghana",
    "GIB": "Gibraltar", "GIN": "Guinea", "GLP": "Guadeloupe", "GMB": "Gambia",
    "GNB": "Guinea-Bissau", "GNQ": "Equatorial Guinea", "GRC": "Greece", "GRD": "Grenada",
    "GRL": "Greenland", "GTM": "Guatemala", "GUF": "French Guiana", "GUM": "Guam",
    "GUY": "Guyana", "HKG": "Hong Kong", "HND": "Honduras", "HRV": "Croatia",
    "HTI": "Haiti", "HUN": "Hungary", "IDN": "Indonesia", "IMN": "Isle of Man",
    "IND": "India", "IRL": "Ireland", "IRQ": "Iraq", "ISL": "Iceland",
    "ISR": "Israel", "ITA": "Italy", "JAM": "Jamaica", "JEY": "Jersey",
    "JOR": "Jordan", "JPN": "Japan", "KAZ": "Kazakhstan", "KEN": "Kenya",
    "KGZ": "Kyrgyzstan", "KHM": "Cambodia", "KIR": "Kiribati", "KNA": "Saint Kitts and Nevis",
    "KOR": "South Korea", "KWT": "Kuwait", "LAO": "Laos", "LBN": "Lebanon",
    "LBR": "Liberia", "LBY": "Libya", "LCA": "Saint Lucia", "LIE": "Liechtenstein",
    "LKA": "Sri Lanka", "LSO": "Lesotho", "LTU": "Lithuania", "LUX": "Luxembourg",
    "LVA": "Latvia", "MAC": "Macau", "MAR": "Morocco", "MCO": "Monaco",
    "MDA": "Moldova", "MDG": "Madagascar", "MDV": "Maldives", "MEX": "Mexico",
    "MHL": "Marshall Islands", "MKD": "North Macedonia", "MLI": "Mali", "MLT": "Malta",
    "MMR": "Myanmar", "MNE": "Montenegro", "MNG": "Mongolia", "MNP": "Northern Mariana Islands",
    "MOZ": "Mozambique", "MRT": "Mauritania", "MSR": "Montserrat", "MTQ": "Martinique",
    "MUS": "Mauritius", "MWI": "Malawi", "MYS": "Malaysia", "MYT": "Mayotte",
    "NAM": "Namibia", "NCL": "New Caledonia", "NER": "Niger", "NFK": "Norfolk Island",
    "NGA": "Nigeria", "NIC": "Nicaragua", "NIU": "Niue", "NLD": "Netherlands",
    "NOR": "Norway", "NPL": "Nepal", "NRU": "Nauru", "NZL": "New Zealand",
    "OMN": "Oman", "PAK": "Pakistan", "PAN": "Panama", "PER": "Peru",
    "PHL": "Philippines", "PLW": "Palau", "PNG": "Papua New Guinea", "POL": "Poland",
    "PRI": "Puerto Rico", "PRT": "Portugal", "PRY": "Paraguay", "PSE": "Palestine",
    "PYF": "French Polynesia", "QAT": "Qatar", "REU": "Réunion", "ROU": "Romania",
    "RUS": "Russia", "RWA": "Rwanda", "SAU": "Saudi Arabia", "SEN": "Senegal",
    "SGP": "Singapore", "SHN": "Saint Helena", "SLB": "Solomon Islands", "SLE": "Sierra Leone",
    "SLV": "El Salvador", "SMR": "San Marino", "SOM": "Somalia", "SPM": "Saint Pierre and Miquelon",
    "SRB": "Serbia", "SSD": "South Sudan", "STP": "São Tomé and Príncipe", "SUR": "Suriname",
    "SVK": "Slovakia", "SVN": "Slovenia", "SWE": "Sweden", "SWZ": "Eswatini", "SXM": "Sint Maarten",
    "SYC": "Seychelles", "TCA": "Turks and Caicos Islands", "TCD": "Chad", "TGO": "Togo",
    "THA": "Thailand", "TJK": "Tajikistan", "TKM": "Turkmenistan", "TLS": "Timor-Leste",
    "TON": "Tonga", "TTO": "Trinidad and Tobago", "TUN": "Tunisia", "TUR": "Turkey",
    "TUV": "Tuvalu", "TWN": "Taiwan", "TZA": "Tanzania", "UGA": "Uganda", "UKR": "Ukraine",
    "UMI": "U.S. Minor Outlying Islands", "URY": "Uruguay", "USA": "United States", "UZB": "Uzbekistan",
    "VAT": "Vatican City", "VCT": "Saint Vincent and the Grenadines", "VEN": "Venezuela",
    "VGB": "British Virgin Islands", "VIR": "U.S. Virgin Islands", "VNM": "Vietnam", "VUT": "Vanuatu",
    "WLF": "Wallis and Futuna", "WSM": "Samoa", "XKS": "Kosovo", "YEM": "Yemen",
    "ZAF": "South Africa", "ZMB": "Zambia", "ZWE": "Zimbabwe"
}

# ========= JWT TOKEN =========
def create_token():
    now = int(time.time())
    payload = {
        "iss": ASC_ISSUER_ID,
        "iat": now,
        "exp": now + 1200,
        "aud": "appstoreconnect-v1",
    }
    headers = {"alg": "ES256", "kid": ASC_KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, ASC_PRIVATE_KEY, algorithm="ES256", headers=headers)

# ========= HENT ALLE REVIEWS =========
def fetch_reviews(token):
    """Hent alle reviews med tekst"""
    url = f"https://api.appstoreconnect.apple.com/v1/apps/{APP_ID}/customerReviews?limit=200"
    headers = {"Authorization": f"Bearer {token}"}
    reviews = []

    while url:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            attr = item.get("attributes", {})
            territory = r.get("territory", "UNKNOWN")
            reviews.append({
                "id": item.get("id"),
                "rating": attr.get("rating"),
                "title": attr.get("title", ""),
                "review": attr.get("body", ""),
                "reviewerNickname": attr.get("reviewerNickname", ""),
                "createdDate": attr.get("createdDate", ""),
                "territory": attr.get("territory", ""),
                "country_name": COUNTRY_NAMES.get(territory, territory)
            })
        url = data.get("links", {}).get("next")

    return reviews

# ========= Summarize ratings =========
def summarize_ratings(reviews):
    stars = {"5":0,"4":0,"3":0,"2":0,"1":0}
    total = 0
    sum_rating = 0
    country_data = defaultdict(list)

    for r in reviews:
        rating = r.get("rating")
        territory = r.get("territory", "UNKNOWN")
        country_name = COUNTRY_NAMES.get(territory, territory)
        if rating:
            rating_str = str(rating)
            if rating_str in stars:
                stars[rating_str] += 1
            sum_rating += rating
            total += 1
            country_data[country_name].append(rating)

    average = round(sum_rating / total, 2) if total > 0 else 0

    # Gjennomsnitt per land
    ratings_per_country = {}
    for country, ratings in country_data.items():
        count = len(ratings)
        avg = round(sum(ratings) / count, 2) if count > 0 else 0
        ratings_per_country[country] = {"total_count": count, "average": avg}

    return {"total_count": total, "average": average, "stars": stars, "ratings_per_country": ratings_per_country}

# ========= LAST HISTORIKK =========
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {"ratings": {}, "reviews": [], "review_ids": []}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ========= LAGRE HISTORIKK =========
def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ========= OPPDATER HISTORY =========
def update_history(history, reviews):
    """Legg til nye reviews uten duplikater og oppdater rating summary"""
    existing_ids = set(history.get("review_ids", []))
    new_reviews = [r for r in reviews if r["id"] not in existing_ids]

    if new_reviews:
        print(f"Nye reviews lagt til: {len(new_reviews)}")
        history.setdefault("reviews", []).extend(new_reviews)
        history.setdefault("review_ids", []).extend(r["id"] for r in new_reviews)
    else:
        print("Ingen nye reviews.")

    # Oppdater rating summary
    history["ratings"] = summarize_ratings(history["reviews"])

    # Pakk sammen i ønsket format
    final_history = {
        "ratings": ratings_summary,
        "reviews": history["reviews"],
        "review_ids": history["review_ids"]
    }

    return final_history

# ========= MAIN =========
def main():
    token = create_token()
    reviews = fetch_reviews(token)
    history = load_history()
    history = update_history(history, reviews)
    save_history(history)

    print(f"Totalt reviews lagret: {len(history['reviews'])}")
    print("Rating summary:")
    print(json.dumps(history["ratings"], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
