import logging.config
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
})


import logging

import tinder_client
import threading
import time
import database as db


logger = logging.getLogger(__name__)
database = db.MongoDataStore()
positions = [
    (37.4507, -122.1634),
]

opening_lines = [
    'Early to bed or early to rise?',
]


def _get_random(items):
    return items[0]  # todo: fixme


class UpdatesThread(threading.Thread):
    def __init__(self, last_timestamp, pause_in_seconds):
        super(UpdatesThread, self).__init__()
        self._last_timestamp = last_timestamp
        self._pause_in_seconds = pause_in_seconds

    def run(self):
        while True:
            logger.info('getting updates ... ')
            updates_json = tinder_client.get_updates(self._last_timestamp)

            def get_full_match(match_id):
                return tinder_client.get_match_info(match_id)

            map(lambda m: database.save_match(m['_id'], get_full_match(m['_id'])), updates_json['matches'])
            map(lambda b: database.save_block(b, {'_id': b}), updates_json['blocks'])
            map(lambda l: database.save_list(l['_id'], l), updates_json['lists'])
            map(lambda d: database.save_deleted_list(d['_id'], d), updates_json['deleted_lists'])

            self._last_timestamp = updates_json['last_activity_date']

            logger.info('sleeping for %s seconds ... ' % self._pause_in_seconds)
            time.sleep(self._pause_in_seconds / 1000)


class ProcessRecordsThread(threading.Thread):
    def __init__(self, pause_in_seconds):
        super(ProcessRecordsThread, self).__init__()
        self._pause_in_seconds = pause_in_seconds

    def run(self):
        while True:
            for lat, lng in positions:
                try:
                    self._process_location(lat, lng)
                except:
                    logging.exception('error processing (%s, %s)' % (lat, lng))

                    time.sleep(self._pause_in_seconds)

    def _process_location(self, lat, lng):
        logger.info('posting location ... ')
        tinder_client.set_location(lat, lng)

        logger.info('getting recs ... ')
        while True:
            records = tinder_client.get_records()
            if len(records) == 0:
                logger.info('received zero recs')
                break

            for record in records:
                self._process_record(record)

    def _process_record(self, record):
        record_id = record['_id']

        database.save_record(record_id, record)

        logger.info('liking %s ... ' % record_id)
        like_json = tinder_client.like(record_id)
        database.save_match(record_id, like_json)
        if like_json['match'] is False:
            return

        tinder_client.send_message(
            like_json['match']['_id'],
            _get_random(opening_lines),
        )


def main():
    auth_json = tinder_client.auth(
        'CAAGm0PX4ZCpsBAP8ZCogfY2chw42KUbiepcJjU0YA2x4zlZCe7Y6e3IFLfyZBThfBIEFLnxIUjUpuEDOX'
        'QMY0FxPOEnNW2tIhSR63Sjfrr52u3lp6M8QDbIzZC5ZAnHEydftDWKkVmzVNwmeeRsCgZA52RMxtE9uMY0'
        'YZBTkS7fx4QP6yPZB9xkQ0BxbvlOX2KXY5NlUNznP7lsIeOXZAeb4z1tVfwTcTH0NHbKIRrMso7ZBgZDZD'
    )

    tinder_client.common_headers['X-Auth-Token'] = auth_json['token']
    tinder_client.max_records_per_request = auth_json['globals']['recs_size']

    sleep_between_updates = int(auth_json['globals']['updates_interval'])

    updates_thread = UpdatesThread(None, sleep_between_updates)
    updates_thread.start()

    process_records_thread = ProcessRecordsThread(sleep_between_updates)
    process_records_thread.start()

    updates_thread.join()
    process_records_thread.join()


if __name__ == '__main__':
    main()