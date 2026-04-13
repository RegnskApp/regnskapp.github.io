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

// Merge countries
function mergeCountries(target, source) {
  if (!source) return;
  for (const [country, value] of Object.entries(source)) {
    target[country] = (target[country] || 0) + value;
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

    // ✅ Hent riktige felter fra begge
    const ascCountries = ascData.total_per_country;
    const playCountries = playData.by_country;

    mergeCountries(combinedCountries, ascCountries);
    mergeCountries(combinedCountries, playCountries);

    // Sorter
    const sortedCountries = Object.entries(combinedCountries)
      .sort((a, b) => b[1] - a[1]);

    const top10 = sortedCountries.slice(0, 10).map(([country, downloads]) => ({
      country,
      downloads,
    }));

    // ✅ Total downloads (forskjellige feltnavn!)
    const totalDownloads =
      (ascData.total_units_all_time || 0) +
      (playData.total_downloads || 0);

    // ✅ Datoer (forskjellige feltnavn!)
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
      top_10: top10,
    };

    fs.writeFileSync(
      "data/global_stats.json",
      JSON.stringify(output, null, 2)
    );

    console.log("✅ global_stats.json updated successfully");
  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
})();
