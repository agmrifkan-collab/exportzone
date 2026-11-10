tools/fonts_subset.py
=====================

The site loads small per-weight font files (fonts/*.s.woff2). Each one holds
only the characters that weight actually shows on the pages. The full fonts
(fonts/*.woff2 without ".s") stay in the repo as the source files.

Run this again after ANY text change on the site (new headline, new page,
new caption). A character that is missing from the subset is drawn with the
device's own font and looks different from the rest of the line.

    pip install fonttools brotli playwright
    python3 tools/fonts_subset.py .

It opens every *.html page (except google*.html and index_1.html) at three
screen widths, rebuilds fonts/*.s.woff2 and fonts/subset-chars.json, and
keeps the pages pointing at the .s.woff2 files. Safe to run repeatedly.
