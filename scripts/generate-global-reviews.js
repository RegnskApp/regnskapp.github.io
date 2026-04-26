const fs = require("fs");

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}`);
  return res.json();
}

function formatDate(dateString) {
  if (!dateString) return null;

  return String(dateString)
    .split("T")[0]
    .split(" ")[0];
}

function safeNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function getStarsObject() {
  return {
    "5": 0,
    "4": 0,
    "3": 0,
    "2": 0,
    "1": 0
  };
}

function addStars(target, source) {
  if (!source) return;

  for (const star of ["5", "4", "3", "2", "1"]) {
    target[star] += safeNumber(source[star]);
  }
}

function calculateAverageFromStars(stars) {
  const total =
    stars["5"] +
    stars["4"] +
    stars["3"] +
    stars["2"] +
    stars["1"];

  if (total === 0) return 0;

  const sum =
    stars["5"] * 5 +
    stars["4"] * 4 +
    stars["3"] * 3 +
    stars["2"] * 2 +
    stars["1"] * 1;

  return Number((sum / total).toFixed(2));
}

function normalizeAppStoreReviews(reviews) {
  if (!Array.isArray(reviews)) return [];

  return reviews.map((review) => ({
    source: "app_store",
    store: "App Store",
    id: review.id || null,
    date: formatDate(review.createdDate),
    rating: safeNumber(review.rating),
    title: review.title || "",
    text: review.review || "",
    reviewer: review.reviewerNickname || "",
    country: review.country_name || null,
    territory: review.territory || null,
    link: null
  }));
}

function normalizePlayStoreReviews(reviews) {
  if (!Array.isArray(reviews)) return [];

  return reviews.map((review, index) => ({
    source: "play_store",
    store: "Google Play",
    id: `play-${formatDate(review.date) || "unknown"}-${index + 1}`,
    date: formatDate(review.date),
    rating: safeNumber(review.rating),
    title: review.title || "",
    text: review.text || "",
    reviewer: "",
    country: null,
    territory: null,
    link: review.link || null,
    file_updated: formatDate(review.file_updated)
  }));
}

(async () => {
  try {
    const ascUrl = "https://balancetrackr.com/data/asc_reviews.json";
    const playUrl = "https://balancetrackr.com/data/play_store_reviews.json";

    const [ascData, playData] = await Promise.all([
      fetchJSON(ascUrl),
      fetchJSON(playUrl)
    ]);

    const combinedStars = getStarsObject();

    // App Store ratings
    addStars(combinedStars, ascData?.ratings?.stars);

    // Google Play reviews/ratings
    addStars(combinedStars, playData?.by_rating);

    const totalReviews =
      safeNumber(ascData?.ratings?.total_count) +
      safeNumber(playData?.total_reviews);

    const averageRating = calculateAverageFromStars(combinedStars);

    const appStoreReviews = normalizeAppStoreReviews(ascData?.reviews);
    const playStoreReviews = normalizePlayStoreReviews(playData?.reviews);

    const reviews = [...appStoreReviews, ...playStoreReviews]
      .filter((review) => review.rating > 0)
      .sort((a, b) => {
        const dateA = a.date || "";
        const dateB = b.date || "";

        if (dateA !== dateB) {
          return dateA.localeCompare(dateB);
        }

        return a.source.localeCompare(b.source);
      });

    const appStoreLastUpdated = formatDate(ascData?.last_review_update);
    const playStoreLastUpdated = formatDate(playData?.last_updated);

    const lastUpdated =
      [appStoreLastUpdated, playStoreLastUpdated]
        .filter(Boolean)
        .sort()
        .pop() || new Date().toISOString().split("T")[0];

    const output = {
      last_updated: lastUpdated,

      total_reviews: totalReviews,
      written_reviews: reviews.length,
      average_rating: averageRating,

      by_rating: combinedStars,

      sources: {
        app_store: {
          last_updated: appStoreLastUpdated,
          total_reviews: safeNumber(ascData?.ratings?.total_count),
          written_reviews: appStoreReviews.length,
          average_rating: safeNumber(ascData?.ratings?.average),
          by_rating: ascData?.ratings?.stars || getStarsObject()
        },
        play_store: {
          last_updated: playStoreLastUpdated,
          total_reviews: safeNumber(playData?.total_reviews),
          written_reviews: playStoreReviews.length,
          average_rating: safeNumber(playData?.average_rating),
          by_rating: playData?.by_rating || getStarsObject()
        }
      },

      reviews
    };

    fs.writeFileSync(
      "data/global_reviews.json",
      JSON.stringify(output, null, 2)
    );

    console.log("✅ global_reviews.json updated successfully");
    console.log(`⭐ Average rating: ${output.average_rating}`);
    console.log(`📝 Total ratings/reviews: ${output.total_reviews}`);
    console.log(`💬 Written reviews: ${output.written_reviews}`);
    console.log(`🍎 App Store: ${output.sources.app_store.total_reviews}`);
    console.log(`🤖 Play Store: ${output.sources.play_store.total_reviews}`);

  } catch (error) {
    console.error("❌ Error:", error);
    process.exit(1);
  }
})();
