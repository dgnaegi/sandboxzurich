#!/bin/sh
# Upload the locally generated world data (tiles + textures + loading posters, not in git) as GitHub release "world-data".
# Run after a pipeline build; the deploy workflow downloads it on every push.
set -e
cd "$(dirname "$0")/.."
# loading posters are jpg (no images in git, .gitignore) -> they travel with the world data
tar -czf /tmp/world-data.tar.gz -C web/public tiles tex loading/poster.jpg loading/poster_p.jpg
gh release view world-data >/dev/null 2>&1 || gh release create world-data --title "World data" --notes "Generated tiles and textures for the deploy workflow"
gh release upload world-data /tmp/world-data.tar.gz --clobber
echo "uploaded $(du -h /tmp/world-data.tar.gz | cut -f1)"
