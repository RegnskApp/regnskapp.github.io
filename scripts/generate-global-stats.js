const fs = require("fs");

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}`);
  return res.json();
}

// Normaliser dato til YYYY-MM-DD
function formatDate(dateString) {
  if (!dateString) return null;
  return dateString.split(" ")[0];
}

// Normaliser landnavn
function normalizeCountryName(name) {
  const map = {
    "Türkiye": "Turkey",
    "Korea, Republic of": "South Korea",
    "United States of America": "United States",
    "UAE": "United Arab Emirates"
  };

  return map[name] || name;
}

// ISO-koder for flagg
function getCountryCode(countryName) {
  const codes = {
    "Afghanistan": "af",
    "Albania": "al",
    "Algeria": "dz",
    "Argentina": "ar",
    "Australia": "au",
    "Austria": "at",
    "Bahrain": "bh",
    "Bangladesh": "bd",
    "Belgium": "be",
    "Brazil": "br",
    "Bulgaria": "bg",
    "Canada": "ca",
    "Chile": "cl",
    "China": "cn",
    "China mainland": "cn",
    "Colombia": "co",
    "Croatia": "hr",
    "Cyprus": "cy",
    "Czech Republic": "cz",
    "Denmark": "dk",
    "Egypt": "eg",
    "Estonia": "ee",
    "Finland": "fi",
    "France": "fr",
    "Germany": "de",
    "Greece": "gr",
    "Hong Kong": "hk",
    "Hungary": "hu",
    "Iceland": "is",
    "India": "in",
    "Indonesia": "id",
    "Iraq": "iq",
    "Ireland": "ie",
    "Israel": "il",
    "Italy": "it",
    "Japan": "jp",
    "Jordan": "jo",
    "Kuwait": "kw",
    "Latvia": "lv",
    "Lebanon": "lb",
    "Lithuania": "lt",
    "Luxembourg": "lu",
    "Malaysia": "my",
    "Mexico": "mx",
    "Morocco": "ma",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Nigeria": "ng",
    "Norway": "no",
    "Oman": "om",
    "Pakistan": "pk",
    "Philippines": "ph",
    "Poland": "pl",
    "Portugal": "pt",
    "Qatar": "qa",
    "Romania": "ro",
    "Russia": "ru",
    "Saudi Arabia": "sa",
    "Serbia": "rs",
    "Singapore": "sg",
    "Slovakia": "sk",
    "Slovenia": "si",
    "South Africa": "za",
    "South Korea": "kr",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Taiwan": "tw",
    "Thailand": "th",
    "Turkey": "tr",
    "Türkiye": "tr",
    "Ukraine": "ua",
    "United Arab Emirates": "ae",
    "United Kingdom": "gb",
    "United States": "us",
    "Vietnam": "vn"
  };

  return codes[countryName] || null;
}

// Merge countries med normalisering
function mergeCountries(target, source) {
  if (!source) return;

  for (const [country, value] of Object.entries(source)) {
    const normalized = normalizeCountryName(country);
    target[normalized] = (target[normalized] || 0) + value;
  }
}

(async () => {
  try {
    const ascUrl = "https://balancetrackr.com/data/asc_history.json";
    const playUrl = "https://balancetrackr.com/data/play_store_history.json";

    const [ascData, playData] = await Promise.all([
      fetchJSON(ascUrl),
      fetchJSON(playUrl),
    ]);

    const combinedCountries = {};

    // Hent riktige felter
    mergeCountries(combinedCountries, ascData.total_per_country);
    mergeCountries(combinedCountries, playData.by_country);

    // Sorter land
    const sortedCountries = Object.entries(combinedCountries)
      .sort((a, b) => b[1] - a[1]);

    // Top 10 med ISO-kode
    const top10 = sortedCountries.slice(0, 10).map(([country, downloads]) => ({
      country,
      code: getCountryCode(country),
      downloads,
    }));

    // Total downloads
    const totalDownloads =
      (ascData.total_units_all_time || 0) +
      (playData.total_installs || 0);

    // Datoer
    const ascDate = formatDate(ascData.last_data_update);
    const playDate = formatDate(playData.last_updated);

    const lastUpdated = [ascDate, playDate]
      .filter(Boolean)
      .sort()
      .pop() || new Date().toISOString().split("T")[0];

    const output = {
      total_downloads: totalDownloads,
      countries: sortedCountries.length,
      last_updated: lastUpdated,
      top_10: top10
    };

    fs.writeFileSync(
      "data/global_stats.json",
      JSON.stringify(output, null, 2)
    );

    console.log("✅ global_stats.json updated successfully");
    console.log(`🌍 Countries: ${output.countries}`);
    console.log(`⬇️ Total downloads: ${output.total_downloads}`);

    const missingCodes = top10.filter(item => !item.code);
    if (missingCodes.length > 0) {
      console.log("⚠️ Missing country codes for:");
      missingCodes.forEach(item => console.log(`- ${item.country}`));
    }

  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
})();
