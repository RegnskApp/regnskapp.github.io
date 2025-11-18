#!/bin/bash

# Languages that were fully localized before the layout update
LOCALIZED_LANGUAGES="de da es fi fr hi it ja nl uk zhHans zhHant"

for lang in $LOCALIZED_LANGUAGES; do
    echo "Restoring localized content for $lang..."

    # Get the original file before our changes
    git show abfb622~1:support/$lang.html > support/${lang}_original.html

    # Extract the content section from original file
    # Find where content starts (after the first h1)
    awk '/<h1>/{found=1; print; next} found' support/${lang}_original.html | head -n -2 > ${lang}_content.txt

    # Update the new file with localized content
    # First, find content boundaries in new file
    content_start=$(grep -n "<!-- Main Content -->" support/$lang.html | cut -d: -f1)
    content_end=$(grep -n "<footer class=\"footer\">" support/$lang.html | cut -d: -f1)
    content_end=$((content_end - 1))

    # Replace content section
    awk -v start="$content_start" -v end="$content_end" 'NR < start || NR > end' support/$lang.html > temp_${lang}_header.txt
    head -n $((start + 1)) temp_${lang}_header.txt > temp_${lang}_final.txt
    cat ${lang}_content.txt >> temp_${lang}_final.txt
    awk -v end="$content_end" 'NR > end' support/$lang.html >> temp_${lang}_final.txt
    mv temp_${lang}_final.txt support/$lang.html

    # Update title to use RegnskApp instead of BalanceTrackr
    sed -i '' "s/BalanceTrackr/RegnskApp/g" support/$lang.html

    # Clean up
    rm -f support/${lang}_original.html ${lang}_content.txt temp_${lang}_header.txt

    echo "✓ Restored $lang"
done

echo "All localized support pages restored!"
