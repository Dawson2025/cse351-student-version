"""
Course    : CSE 351
Assignment: 04
Student   : <your name here>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""
import time
import queue
import threading
import http.client
import json
import socket
from urllib.parse import urlparse

from common import *

from cse351 import *

_parsed = urlparse(TOP_API_URL)
SERVER_HOST = _parsed.hostname or '127.0.0.1'
SERVER_PORT = _parsed.port or (443 if _parsed.scheme == 'https' else 80)

THREADS = 220
WORKERS = 60
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def retrieve_weather_data(command_queue, data_queue):
    connection = None

    while True:
        command = command_queue.get()
        if command is None:
            command_queue.task_done()
            break

        city, record_no = command
        payload = None

        while payload is None:
            try:
                if connection is None:
                    connection = http.client.HTTPConnection(
                        SERVER_HOST,
                        SERVER_PORT,
                        timeout=10,
                    )

                path = f'/record/{city}/{record_no}'
                connection.request('GET', path)
                response = connection.getresponse()

                if response.status != 200:
                    response.read()
                    raise http.client.HTTPException(
                        f'Unexpected status: {response.status} {response.reason}'
                    )

                payload = json.loads(response.read().decode('utf-8'))

            except (socket.timeout, ConnectionError, http.client.HTTPException, OSError, ValueError) as ex:
                if connection is not None:
                    connection.close()
                    connection = None
                time.sleep(0.01)

        if payload is not None:
            data_queue.put((payload['city'], record_no, payload['date'], payload['temp']))

        command_queue.task_done()

    if connection is not None:
        connection.close()


# ---------------------------------------------------------------------------
class Worker(threading.Thread):

    def __init__(self, name, data_queue, noaa):
        super().__init__(name=name)
        self._queue = data_queue
        self._noaa = noaa

    def run(self):
        while True:
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                break
            city, record_no, date, temp = item
            self._noaa.add_record(city, record_no, date, temp)
            self._queue.task_done()


# ---------------------------------------------------------------------------
class NOAA:

    def __init__(self, records_to_retrieve):
        self._records_to_retrieve = records_to_retrieve
        self._data = {
            city: {
                'records': [None] * records_to_retrieve,
                'temp_sum': 0.0,
                'count': 0,
                'lock': threading.Lock(),
            }
            for city in CITIES
        }

    def add_record(self, city, record_no, date, temp):
        city_info = self._data.get(city)
        if city_info is None:
            city_info = {
                'records': [None] * self._records_to_retrieve,
                'temp_sum': 0.0,
                'count': 0,
                'lock': threading.Lock(),
            }
            self._data[city] = city_info

        with city_info['lock']:
            if 0 <= record_no < self._records_to_retrieve:
                city_info['records'][record_no] = (date, temp)
                city_info['temp_sum'] += temp
                city_info['count'] += 1

    def get_temp_details(self, city):
        city_info = self._data.get(city)
        if not city_info:
            return 0.0
        with city_info['lock']:
            count = city_info['count']
            if count == 0:
                return 0.0
            return city_info['temp_sum'] / count


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():

    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    records_to_retrieve = RECORDS_TO_RETRIEVE
    noaa = NOAA(records_to_retrieve)

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f'{name:>15}: Records = {city_details[name]['records']:,}')
    print('===================================')

    records = records_to_retrieve

    command_queue = queue.Queue(maxsize=10)
    data_queue = queue.Queue(maxsize=10)

    workers = [Worker(f'Worker-{i+1}', data_queue, noaa) for i in range(WORKERS)]
    for worker in workers:
        worker.start()

    threads = []
    for i in range(THREADS):
        thread = threading.Thread(
            target=retrieve_weather_data,
            args=(command_queue, data_queue),
            name=f'Request-{i+1}',
        )
        thread.start()
        threads.append(thread)

    for city in CITIES:
        total_records = min(records, city_details[city]['records'])
        for record_no in range(total_records):
            command_queue.put((city, record_no))

    for _ in range(len(threads)):
        command_queue.put(None)

    command_queue.join()

    for thread in threads:
        thread.join()

    for _ in range(len(workers)):
        data_queue.put(None)

    data_queue.join()

    for worker in workers:
        worker.join()




    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()

