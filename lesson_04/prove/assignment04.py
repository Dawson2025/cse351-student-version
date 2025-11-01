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

REQUEST_THREAD_COUNT = 200
WORKER_THREAD_COUNT = 10
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def retrieve_weather_data(request_queue, response_queue):
    """Fetch records from the server and place them on the response queue."""
    
    while True:
        command = request_queue.get()
        # Check for stop signal
        if command is None:
            request_queue.task_done()
            break

        city, record_no = command
        
        # Get the weather data from server
        url = f'{TOP_API_URL}/record/{city}/{record_no}'
        payload = get_data_from_server(url)
        
        # Put the data on response queue for workers to process
        if payload is not None:
            # Send tuple with city, date, and temp
            response_queue.put((payload['city'], payload['date'], payload['temp']))
        # else:
        #     print(f'Failed to get data for {city} record {record_no}')

        request_queue.task_done()


# ---------------------------------------------------------------------------
class Worker(threading.Thread):

    def __init__(self, name, response_queue, noaa):
        super().__init__(name=name)
        self._queue = response_queue
        self._noaa = noaa

    def run(self):
        while True:
            record = self._queue.get()
            if record is None:
                self._queue.task_done()
                break
            
            # Process the record
            city, date, temp = record
            # print(f'{self.name}: Processing {city} - {date}')  # Used this for debugging
            self._noaa.add_record(city, date, temp)
            self._queue.task_done()


# ---------------------------------------------------------------------------
class NOAA:
    """Accumulator for per-city temperature data."""

    def __init__(self):
        # Dictionary to store all city data
        # Each city will have a list of records and a running total of temps
        self._city_data = {}
        for city in CITIES:
            self._city_data[city] = {'records': [], 'total_temp': 0.0}
        
        # Lock to protect the data (had issues with race conditions before adding this)
        # All the workers are writing to this at the same time so need to lock it
        self._lock = threading.Lock()

    def add_record(self, city, date, temp):
        """Add a single (date, temp) pair to the specified city."""
        with self._lock:
            # Check if city exists, if not create it
            if city not in self._city_data:
                self._city_data[city] = {'records': [], 'total_temp': 0.0}
            
            self._city_data[city]['records'].append((date, temp))
            self._city_data[city]['total_temp'] += temp

    def get_temp_details(self, city):
        with self._lock:
            if city not in self._city_data:
                return 0.0
            
            city_info = self._city_data[city]
            num_records = len(city_info['records'])
            
            if num_records == 0:
                return 0.0
            
            # Calculate average
            avg_temp = city_info['total_temp'] / num_records
            return avg_temp


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

    # Create the queues
    # Queue between main thread and request threads.
    request_queue = queue.Queue(maxsize=10)
    # Queue between request threads and worker threads.
    response_queue = queue.Queue(maxsize=10)
    
    # print(f'Starting {REQUEST_THREAD_COUNT} request threads and {WORKER_THREAD_COUNT} workers')

    workers = [Worker(f'Worker-{i+1}', response_queue, noaa) for i in range(WORKER_THREAD_COUNT)]
    for worker in workers:
        worker.start()

    request_threads = []
    for i in range(REQUEST_THREAD_COUNT):
        thread = threading.Thread(
            target=retrieve_weather_data,
            args=(request_queue, response_queue),
            name=f'Request-{i+1}',
        )
        thread.start()
        request_threads.append(thread)

    # Put all the work items in the queue
    for city in CITIES:
        total_records = min(records, city_details[city]['records'])
        for record_no in range(total_records):
            request_queue.put((city, record_no))

    # Send stop signal to threads (None means stop)
    # Need to send one for each thread so they all stop
    for _ in range(len(request_threads)):
        request_queue.put(None)

    # Wait until every queued command has been processed.
    request_queue.join()

    for thread in request_threads:
        thread.join()

    # Provide sentinels for the worker threads so they exit gracefully.
    for _ in range(len(workers)):
        response_queue.put(None)

    # Ensure all results have been incorporated before analyzing NOAA data.
    response_queue.join()

    for worker in workers:
        worker.join()




    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()
