"""
Course: CSE 351 
Lesson: L02 team activity
File:   team.py
Author: <Add name here>

Purpose: Retrieve Star Wars details from a server

Instructions:

- This program requires that the server.py program be started in a terminal window.
- The program will retrieve the names of:
    - characters
    - planets
    - starships
    - vehicles
    - species

- the server will delay the request by 0.5 seconds

TODO
- Create a threaded class to make a call to the server where
  it retrieves data based on a URL.  The class should have a method
  called get_name() that returns the name of the character, planet, etc...
- The threaded class should only retrieve one URL.
  
- Speed up this program as fast as you can by:
    - creating as many as you can
    - start them all
    - join them all

"""

from datetime import datetime, timedelta
import threading

from common import *

# Include cse 351 common Python files
from cse351 import *

# global
call_count = 0


class URLFetcher(threading.Thread):
    """Thread that fetches a single URL from the server and stores the name.

    Usage:
        t = URLFetcher(url)
        t.start()
        t.join()
        name = t.get_name()
    """
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.name = None
        self._error = None

    def run(self):
        global call_count
        try:
            item = get_data_from_server(self.url)
            call_count += 1
            # some items may not have a 'name' key (e.g., films), fall back to title
            self.name = item.get('name') or item.get('title')
        except Exception as e:
            self._error = e

    def get_name(self):
        if self._error:
            raise self._error
        return self.name

def get_urls(film6, kind):
    global call_count

    urls = film6[kind]
    print(kind)

    # create one thread per URL
    threads = [URLFetcher(url) for url in urls]

    # start all threads
    for t in threads:
        t.start()

    # join all threads and print results
    for t in threads:
        t.join()
        try:
            name = t.get_name()
        except Exception as e:
            name = f'<error: {e}>'
        print(f'  - {name}')

def main():
    global call_count

    log = Log(show_terminal=True)
    log.start_timer('Starting to retrieve data from the server')

    film6 = get_data_from_server(f'{TOP_API_URL}/films/6')
    call_count += 1
    print_dict(film6)

    # Retrieve people
    get_urls(film6, 'characters')
    get_urls(film6, 'planets')
    get_urls(film6, 'starships')
    get_urls(film6, 'vehicles')
    get_urls(film6, 'species')

    log.stop_timer('Total Time To complete')
    log.write(f'There were {call_count} calls to the server')

if __name__ == "__main__":
    main()
