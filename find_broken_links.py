print('Broken Link Finder\n'
      'This script scans a web page of a given URL and validates the links on it\n'
      'If the page has a link to the same hostname as the URL given by the user, its destination page also scanned\n'
      'So potentially the whole site will be scanned (this may take hours!)\n'
      'All broken links found are saved on broken-links-[date]-[time]-[random-ID].txt')

import os
import requests
import validators
import colorama
import queue
import datetime
from random import randint
from selenium import webdriver
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

chrome_ua = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36'}

def validate(link):
    try:
        url = link.get_attribute('href')
        text = link.text.strip()

        try:
            r = requests.get(url, headers=chrome_ua, allow_redirects=True, timeout=5, stream=True)
            return (r.ok, r.status_code, url, text)

        except:
            return (False, 0, url, text)

    except:
        return (False, 0, '', '')

# Colorama setup
colorama.init()

# URL setup
start_page = input('URL: ')

while(not validators.url(start_page)):
    print('Invalid URL')
    start_page = input('URL: ')


parsed_uri = urlparse(start_page)
hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

# Timer setup
start_time = datetime.datetime.now()

# Output file setup
datetime_string = start_time.strftime('%Y-%m-%d-%H-%M-%S')
script_path = os.path.dirname(os.path.abspath(__file__))
file_id = ''.join(['%s' % randint(0, 9) for digit in range(0, 6)])
output_file_path = os.path.join(script_path, 'broken-links-' + datetime_string + '-' + file_id + '.txt')
output_file = open(output_file_path, 'w')

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

# Sets used to flag visited pages/requested URLs and avoid multiple scans/requests
scanned_pages = {start_page}
broken_urls =  set()
''' Uncomment if you want to save good links too
good_urls = set()
'''

# Webdriver setup
options = webdriver.chrome.options.Options()
options.add_argument('--log-level=3') # minimal logging
driver_path = os.path.join(script_path, 'drivers', 'chromedriver.exe')
driver = webdriver.Chrome(driver_path, options=options)
driver.implicitly_wait = 1

# Find the broken links
output_file.write('Broken links found from ' + start_page + '\n')
no_broken_links = True
page_counter = 1
page_total = 1
page_queue = queue.Queue()
page_queue.put(start_page)

while not page_queue.empty():
    page = page_queue.get()
    print('Scanning ' + page + ' (' + str(page_counter) + '/' + str(page_total) + ')')
    page_counter = page_counter + 1
    broken_link_found = False

    try:
        driver.get(page)
        links_to_be_validated = []
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
                    print(colorama.Fore.RED + '\t' + str(link_url) + ' (' + link_text + '): Link found to be broken previously' + colorama.Style.RESET_ALL)
                    
                    if not broken_link_found:
                        broken_link_found = True
                        no_broken_links = False
                        output_file.write('\n' + page + '\n')
                    
                    output_file.write('\t' + str(link_url) + ' (' + link_text + '): Link found to be broken previously' + '\n')
                
                # Uncomment if you want to save good links too
                #elif link_url in good_urls:
                #    print(colorama.Fore.GREEN + '\t' + str(link_url) + ' (' + link_text + '): Link found to be OK previously' + colorama.Style.RESET_ALL)
                
                
                # Link can be validated and is not known to be broken, so put it on the list to be validated
                else:
                    links_to_be_validated.append(link)

    except Exception as err:
            print(colorama.Fore.RED + 'Could not scan ' + page + colorama.Style.RESET_ALL)
            print(str(err))

    # Validate the links asynchronously
    with ThreadPoolExecutor(max_workers=20) as executor:
        req_futures = [executor.submit(validate, requestable_link) for requestable_link in links_to_be_validated]

        for req_future in as_completed(req_futures):
            (req_ok, req_status_code, req_url, req_text) = req_future.result()

            if req_ok:
                ''' Uncomment if you want to save good links too
                print(colorama.Fore.GREEN + '\t' + str(req_url) + ' (' + req_text + '): ' + str(req_status_code) + colorama.Style.RESET_ALL)
                good_urls.add(req_url)
                '''
                
                # If link has the same hostname as the start page AND has not been already scanned, add to scan queue
                req_parsed_uri = urlparse(req_url)
                req_hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=req_parsed_uri)

                if (
                    req_hostname == hostname and
                    req_url not in scanned_pages and
                    not req_url.endswith(do_not_scan)
                    ):
                    
                    print(colorama.Fore.YELLOW + '\t' + req_url + ' added to scan queue' + colorama.Style.RESET_ALL)
                    page_queue.put(req_url)
                    scanned_pages.add(req_url)
                    page_total = page_total + 1 

            # Broken link found
            else:
                print(colorama.Fore.RED + '\t' + str(req_url) + ' (' + req_text + '): ' + str(req_status_code) + colorama.Style.RESET_ALL)
                
                if not broken_link_found:
                    broken_link_found = True
                    no_broken_links = False
                    output_file.write('\n' + page + '\n')

                output_file.write('\t' + str(req_url) + ' (' + req_text + '): ' + str(req_status_code) + '\n')
                broken_urls.add(req_url)

driver.quit()

if no_broken_links:
    output_file.seek(0)
    output_file.truncate()
    output_file.write('No broken links found from ' + start_page + '\n')

running_time = datetime.datetime.now() - start_time
farewell_msg = '\n' + str(page_total) + ' pages scanned in ' + str(running_time)
print('Scan completed!' + farewell_msg)
output_file.write(farewell_msg)
output_file.close()