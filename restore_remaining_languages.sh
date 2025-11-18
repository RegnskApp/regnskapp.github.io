#!/bin/bash

# Remaining localized languages that need restoration
REMAINING_LANGUAGES="da es fi fr hi it ja nl uk zhHans zhHant"

for lang in $REMAINING_LANGUAGES; do
    echo "Restoring $lang..."

    # Get original content
    git show abfb622~1:support/$lang.html | awk '/<h1>/{found=1} found {print}' | sed '$d' | sed '$d' > ${lang}_content.txt

    # Update email address
    sed -i '' 's/olemortentengesdal@icloud.com/balancetrackr@gmail.com/g' ${lang}_content.txt

    # Create full content with proper structure
    cat > ${lang}_content_full.txt << EOF
  <!-- Main Content -->
  <div class="content">
EOF
    cat ${lang}_content.txt >> ${lang}_content_full.txt

    # Add back button and footer
    cat >> ${lang}_content_full.txt << EOF

    <p>
      <a href="../index.html" class="back-btn">← Back to Home</a>
    </p>

  </div>

  <!-- Footer -->
  <footer class="footer">
    <div class="footer-content">
      <p>&copy; 2025 BalanceTrackr (RegnskApp).<br>
      Ole Morten Tengesdal. All rights reserved.</p>
    </div>
  </footer>
EOF

    # Update title to use RegnskApp
    sed -i '' 's/BalanceTrackr/RegnskApp/g' support/$lang.html

    # Replace content section (lines 552-709)
    awk 'NR<552 || NR>709' support/$lang.html > temp_${lang}_header.txt
    awk 'NR<=159' temp_${lang}_header.txt > temp_${lang}_final.txt
    cat ${lang}_content_full.txt >> temp_${lang}_final.txt
    awk 'NR>709' support/$lang.html >> temp_${lang}_final.txt
    mv temp_${lang}_final.txt support/$lang.html

    # Clean up
    rm -f ${lang}_content.txt ${lang}_content_full.txt temp_${lang}_header.txt

    echo "✓ Restored $lang"
done

echo "All remaining languages restored!"
