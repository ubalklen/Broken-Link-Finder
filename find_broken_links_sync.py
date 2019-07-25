### Broken Link Finder
### This script scans a web page of a given URL and validates the links on it
### If a link is working and has the same hostname as the URL given by the user, it's also scanned
### So potentially the whole website will be scanned (if properly linked) 
### All broken links found are saved on out.txt

import os
import requests
import time
import validators
import colorama
import queue 
from selenium import webdriver
from urllib.parse import urlparse

# Requests setup
chrome_ua = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'}

# Colorama setup
colorama.init()

# URL setup
start_page = input('URL: ')

while(not validators.url(start_page)):
    print('Invalid URL')
    start_page = input('URL: ')

start_time = time.time()

parsed_uri = urlparse(start_page)
hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

# We don't want to scan files (only web pages)
do_not_scan = (
               '#',
               '.pdf',
               '.doc',
               '.docx',
               '.xls',
               '.xlsx',
               '.ppt',
               '.pptx',
               '.doc',
               '.docx',
               '.odt',
               '.ods',
               '.jpg',
               '.png',
               '.zip',
               '.rar',
               )

# Also, we don't want to validate special links
do_not_validate = (
                 'javascript:',
                 'mailto:',
                 'tel:',
                 )

# Sets used to flag visited pages/requested URLs and avoid multiple requests
scanned_pages = {start_page}
broken_urls =  set()
#good_urls = set() # Uncomment if you want to save good links too

# Webdriver setup
options = webdriver.chrome.options.Options()
options.add_argument('--log-level=3') # minimal logging
script_path = os.path.dirname(os.path.abspath(__file__))
driver_path = os.path.join(script_path, 'drivers', 'chromedriver.exe')
driver = webdriver.Chrome(driver_path, options=options)

# Find the broken links
page_counter = 1
page_total = 1
page_queue = queue.Queue()
page_queue.put(start_page)
while not page_queue.empty():
    page = page_queue.get()
    print('Scanning ' + page + ' (' + str(page_counter) + '/' + str(page_total) + ')')
    page_counter = page_counter + 1

    try:
        driver.get(page)
        time.sleep(1)
        link_list = driver.find_elements_by_tag_name('a')
        
        for link in link_list:
            link_text = link.text.strip()
            link_url = link.get_attribute('href')

            # Check if link can be validated
            if (
                link_url and
                link_url.strip() and
                not link_url.startswith(do_not_validate)
                ):

                # Check if the link has already found out to be broken (noneed to validate again)
                if link_url in broken_urls:
                    print(colorama.Fore.RED + '\t' + str(link_url) + ' (' + link_text + '): Link was reported broken when a previous page was scanned' + colorama.Style.RESET_ALL)
                
                #elif link_url in good_urls:  # Uncomment if you want to save good links too
                #    print(colorama.Fore.GREEN + '\t' + str(link_url) + ' (' + link_text + '): Link was reported OK when a previous page was scanned' + colorama.Style.RESET_ALL)
                
                # Link can be validated and is not known to be broken, so put it on the list to be validated
                else:
                    try:
                        r = requests.get(link_url, headers=chrome_ua, allow_redirects=True, timeout=5, stream=True)

                        if r.ok:
                            # Uncomment if you want to save good links too
                            #print(colorama.Fore.GREEN + '\t' + str(r.url) + ' (' + r.text + '): ' + str(r.status_code) + colorama.Style.RESET_ALL)
                            #good_urls.add(r.url)
                            
                            # If link has the same hostname as the start page AND has not been already scanned, add to scan queue
                            link_parsed_uri = urlparse(link_url)
                            link_hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=link_parsed_uri)

                            if (
                                link_hostname == hostname and
                                link_url not in scanned_pages and
                                not link_url.endswith(do_not_scan)
                                ):
                                
                                print(colorama.Fore.YELLOW + '\t' + link_url + ' added to scan queue' + colorama.Style.RESET_ALL)
                                page_queue.put(link_url)
                                scanned_pages.add(link_url)
                                page_total = page_total + 1 

                        # Broken link found
                        else:
                            print(colorama.Fore.RED + '\t' + str(link_url) + ' (' + link_text + '): ' + str(r.status_code) + colorama.Style.RESET_ALL)
                            broken_urls.add(link_url)

                    except:
                        print(colorama.Fore.RED + '\t' + str(link_url) + ' (' + link_text + '): Could not validate link' + colorama.Style.RESET_ALL)
                        broken_urls.add(link_url)

    except Exception as err:
            print(colorama.Fore.RED + 'Could not scan ' + page + colorama.Style.RESET_ALL)
            print(str(err))

driver.quit()
running_time = time.time() - start_time
print('Scan completed!')
print(str(page_total) + 'pages scanned in ' + running_time.strftime('%H:%M:%S'))