const fs = require("fs");

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}`);
  return res.json();
}

function mergeCountries(target, source) {
  for (const [country, value] of Object.entries(source)) {
    target[country] = (target[country] || 0) + value;
  }
}

function formatDate(dateString) {
  return dateString.split(" ")[0]; // kun YYYY-MM-DD
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

    mergeCountries(combinedCountries, ascData.by_country || {});
    mergeCountries(combinedCountries, playData.by_country || {});

    const sortedCountries = Object.entries(combinedCountries)
      .sort((a, b) => b[1] - a[1]);

    const top10 = sortedCountries.slice(0, 10).map(([country, downloads]) => ({
      country,
      downloads,
    }));

    const totalDownloads =
      (ascData.total_downloads || 0) +
      (playData.total_downloads || 0);

    const lastUpdated =
      formatDate(ascData.last_updated) > formatDate(playData.last_updated)
        ? formatDate(ascData.last_updated)
        : formatDate(playData.last_updated);

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

    console.log("✅ global_stats.json updated");
  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
})();
