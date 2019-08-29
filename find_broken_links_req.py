print(
    "Broken Link Finder (no-Selenium version)\n"
    "This script scans a web page of a given URL and validates the links on it\n"
    "If the page has a link to the same hostname as the URL given by the user, its destination page also scanned\n"
    "So potentially the whole site will be scanned (this may take hours!)\n"
    "All broken links found are saved on broken-links-[date]-[time]-[random-ID].txt"
)

import os
import requests
from bs4 import BeautifulSoup
import validators
import colorama
import queue
import datetime
from random import randint
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

chrome_ua = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
}


def validate(link):
    (url, text) = link

    try:
        r_head = requests.head(url, headers=chrome_ua, allow_redirects=True, timeout=10)

        if r_head.ok:
            return (True, r_head.status_code, url, text, "")

        else:
            try:
                r_get = requests.get(
                    url,
                    headers=chrome_ua,
                    allow_redirects=True,
                    stream=True,
                    timeout=10,
                )
                return (r_get.ok, r_get.status_code, url, text, "")

            except Exception as get_e:
                return (False, 0, url, text, str(get_e))

    except Exception:
        try:
            r_get = requests.get(
                url, headers=chrome_ua, allow_redirects=True, stream=True, timeout=10
            )
            return (r_get.ok, r_get.status_code, url, text, "")

        except Exception as head_e:
            return (False, 0, url, text, str(head_e))


# Colorama setup
colorama.init()

# URL setup
start_page = input("URL: ")

while not validators.url(start_page):
    print("Invalid URL")
    start_page = input("URL: ")


parsed_uri = urlparse(start_page)
hostname = "{uri.scheme}://{uri.netloc}/".format(uri=parsed_uri)

# Timer setup
start_time = datetime.datetime.now()

# Output file setup
datetime_string = start_time.strftime("%Y-%m-%d-%H-%M-%S")
script_path = os.path.dirname(os.path.abspath(__file__))
file_id = "".join(["%s" % randint(0, 9) for digit in range(0, 6)])
output_file_path = os.path.join(
    script_path, "broken-links-" + datetime_string + "-" + file_id + ".txt"
)
output_file = open(output_file_path, "w", encoding="utf-8")

# We don't want to scan files (only web pages)
do_not_scan = (
    "#",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".doc",
    ".docx",
    ".odt",
    ".ods",
    ".jpg",
    ".png",
    ".zip",
    ".rar",
)

# Also, we don't want to validate special links
do_not_validate = ("#", "javascript:", "mailto:", "tel:")

# Sets used to flag visited pages/requested URLs and avoid multiple scans/requests
scanned_pages = {start_page}
broken_urls = set()
ok_urls = set()

# Find the broken links
output_file.write("Broken links found from " + start_page + "\n")
no_broken_links = True
page_counter = 1
page_total = 1
page_queue = queue.Queue()
page_queue.put(start_page)

while not page_queue.empty():
    page = page_queue.get()
    print("Scanning " + page + " (" + str(page_counter) + "/" + str(page_total) + ")")
    page_counter = page_counter + 1
    broken_link_found = False

    try:
        r = requests.get(page, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        links_to_be_validated = set()
        link_list = soup.find_all("a", href=True)

        for link in link_list:
            if link["href"].startswith("/"):
                link_url = start_page + link["href"]
            else:
                link_url = link["href"]

            link_text = link.text.strip()

            # Check if link can or needed to be validated
            if (
                link_url
                and link_url.strip()
                and not link_url.startswith(do_not_validate)
                and not link in ok_urls
            ):

                # Check if the link has already found out to be broken (it will not be validated again)
                if link_url in broken_urls:
                    if not broken_link_found:
                        broken_link_found = True
                        no_broken_links = False
                        output_file.write("\n" + page + "\n")

                    output_file.write(
                        "\t"
                        + str(link_url)
                        + " ("
                        + link_text
                        + "): Link found to be broken previously"
                        + "\n"
                    )
                    print(
                        colorama.Fore.RED
                        + "\t"
                        + str(link_url)
                        + " ("
                        + link_text
                        + "): Link found to be broken previously"
                        + colorama.Style.RESET_ALL
                    )

                # Link can be validated and is not known to be OK or broken, so put it on the list to be validated
                else:
                    links_to_be_validated.add((link_url, link_text))

    except Exception as err:
        print(colorama.Fore.RED + "Could not scan " + page + colorama.Style.RESET_ALL)
        print(str(err))

    # Validate the links asynchronously
    with ThreadPoolExecutor(max_workers=20) as executor:
        req_futures = [
            executor.submit(validate, requestable_link)
            for requestable_link in links_to_be_validated
        ]

        for req_future in as_completed(req_futures):
            (
                req_ok,
                req_status_code,
                req_url,
                req_text,
                req_exception_text,
            ) = req_future.result()

            if req_ok:
                ok_urls.add(req_url)

                # If link has the same hostname as the start page AND has not been already scanned, add to scan queue
                req_parsed_uri = urlparse(req_url)
                req_hostname = "{uri.scheme}://{uri.netloc}/".format(uri=req_parsed_uri)

                if (
                    req_hostname == hostname
                    and req_url not in scanned_pages
                    and not req_url.endswith(do_not_scan)
                ):
                    page_queue.put(req_url)
                    scanned_pages.add(req_url)
                    page_total = page_total + 1
                    print(
                        colorama.Fore.YELLOW
                        + "\t"
                        + req_url
                        + " added to scan queue"
                        + colorama.Style.RESET_ALL
                    )

            # Broken link found
            else:
                if not broken_link_found:
                    broken_link_found = True
                    no_broken_links = False
                    output_file.write("\n" + page + "\n")

                if req_exception_text == "":
                    print(
                        colorama.Fore.RED
                        + "\t"
                        + str(req_url)
                        + " ("
                        + req_text
                        + "): "
                        + str(req_status_code)
                        + colorama.Style.RESET_ALL
                    )
                    output_file.write(
                        "\t"
                        + str(req_url)
                        + " ("
                        + req_text
                        + "): "
                        + str(req_status_code)
                        + "\n"
                    )

                else:
                    print(
                        colorama.Fore.RED
                        + "\t"
                        + str(req_url)
                        + " ("
                        + req_text
                        + "): "
                        + req_exception_text
                        + colorama.Style.RESET_ALL
                    )
                    output_file.write(
                        "\t"
                        + str(req_url)
                        + " ("
                        + req_text
                        + "): "
                        + req_exception_text
                        + "\n"
                    )

                broken_urls.add(req_url)

if no_broken_links:
    output_file.seek(0)
    output_file.truncate()
    output_file.write("No broken links found from " + start_page + "\n")

running_time = datetime.datetime.now() - start_time
farewell_msg = "\n" + str(page_total) + " pages scanned in " + str(running_time)
print("Scan completed!" + farewell_msg)
output_file.write(farewell_msg)
output_file.close()
