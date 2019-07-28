# Broken Link Finder
A Python script that scans a web page of a given URL and validates the links on it.

If the page has a link to the same hostname as the URL given by the user, its destination page also scanned. It works like a web crawler, so potentially the whole site will be scanned. Be aware that this may take hours.

All broken links found are saved on *broken-links-[date]-[time]-[random-ID].txt*.

# Requisites
Chrome 75 (put the [proper driver](http://chromedriver.chromium.org/downloads) in [drivers](https://github.com/ubalklen/Broken-Link-Finder/tree/master/drivers) folder if you have another version)

Python 3 (it has been tested on Python 3.7)

Some additional Python modules (check the [script](https://github.com/ubalklen/Broken-Link-Finder/blob/master/find_broken_links.py))

# Details
The script scans pages using [Selenium](https://selenium-python.readthedocs.io/) to account for links that may be injected via JavaScript.

Then, each found link is validate with [Requests](https://2.python-requests.org/) in a concurrent (multi-thread) fashion.

A [single-thread script](https://github.com/ubalklen/Broken-Link-Finder/blob/master/find_broken_links_sync.py) is provided for benchmarking.

# TODO
* Better exception handling
* Validate links in other tags besides `<href a=...>` (like `<img src=...>`) 
* Timeout
* Link depth limit
* Proxy support
* NTLM support
* Selenium driver parallelization
