WORDPRESS PAGE 3175 — CARTOFREAKO × SETOUCHI

Canonical permalink: https://benjamin.dekosnik.com/futures/setouchi-2028/
Editor preview: https://benjamin.dekosnik.com/?page_id=3175&preview=true

page-content.html contains core Gutenberg blocks for the existing page.
preview.html is the complete local preview, with working image/PDF links.
The canonical site and its preview were unavailable to the web reader; no
authenticated WordPress tool is connected. This package does not publish.

To install: upload the seven assets in media-manifest.json to WordPress
or the site file host (the World PDF may exceed the Media Library limit).
Write a JSON object mapping every manifest path to its final HTTPS URL.
Rebuild only the block fragment with:
  python3 scripts/build-setouchi-proposal.py --wordpress-only \
    --wordpress-media-map /path/to/media-urls.json
Paste page-content.html into page 3175 using the WordPress code editor;
use the title and excerpt in page.json. Keep the existing parent and
permalink. Preview all image and download links before publishing.

Relative ../ URLs in an unrebound fragment are for the local preview;
use the media map before pasting it into the live WordPress editor.
