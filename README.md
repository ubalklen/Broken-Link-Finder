# Broken Link Finder
A Python script that scans a web page of a given URL and validates the links on it.

If the page has a link to the same hostname as the URL given by the user, its destination page also scanned, like a web crawler, so potentially the whole site will be scanned (this may take hours!).

All broken links found are saved on broken-links-[date]-[time]-[random-ID].txt
