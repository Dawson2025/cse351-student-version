"""
Course    : CSE 351
Assignment: 04
Student   : Dawson Packer

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
import requests

from common import *

from cse351 import *

THREADS = 160
WORKERS = 10
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def retrieve_weather_data(command_queue, data_queue):
    session = requests.Session()

    while True:
        command = command_queue.get()
        if command is None:
            command_queue.task_done()
            break

        city, record_no = command
        try:
            response = session.get(f'{TOP_API_URL}/record/{city}/{record_no}', timeout=10)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException:
            payload = get_data_from_server(f'{TOP_API_URL}/record/{city}/{record_no}')

        if payload is not None:
            data_queue.put((payload['city'], payload['date'], payload['temp']))

        command_queue.task_done()

    session.close()


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
            city, date, temp = item
            self._noaa.add_record(city, date, temp)
            self._queue.task_done()


# ---------------------------------------------------------------------------
class NOAA:

    def __init__(self):
        self._data = {
            city: {'records': [], 'temp_sum': 0.0, 'lock': threading.Lock()}
            for city in CITIES
        }

    def add_record(self, city, date, temp):
        city_info = self._data.get(city)
        if city_info is None:
            city_info = {'records': [], 'temp_sum': 0.0, 'lock': threading.Lock()}
            self._data[city] = city_info

        with city_info['lock']:
            city_info['records'].append((date, temp))
            city_info['temp_sum'] += temp

    def get_temp_details(self, city):
        city_info = self._data.get(city)
        if not city_info:
            return 0.0
        with city_info['lock']:
            records = city_info['records']
            if not records:
                return 0.0
            return city_info['temp_sum'] / len(records)


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

    noaa = NOAA()

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

    records = RECORDS_TO_RETRIEVE

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

