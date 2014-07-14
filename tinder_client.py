import json
import logging
import requests

logger = logging.getLogger(__name__)

host = 'https://api.gotinder.com'

max_records_per_request = 40

common_headers = {
    'app_version': '633',
    'platform': 'android',
    'User-Agent': 'Tinder Android Version 2.2.3',
    'X-Auth-Token': '',
    'os_version': '19',
    'Content-Type': 'application/json; charset=utf-8',
}


class TinderApiError(Exception):
    pass


_session = requests.session()


def _make_api_call(method, path, payload=None):
    if isinstance(payload, dict):
        payload = json.dumps(payload)

    response = _session.request(
        method,
        host + path,
        headers=common_headers,
        data=payload)
    response.raise_for_status()

    return response.json()


def auth(facebook_token):
    auth_json = _make_api_call(
        'POST',
        '/auth',
        {"facebook_token": facebook_token},
    )

    return auth_json


def set_location(lat, lng):
    loc_json = _make_api_call(
        'POST',
        '/user/ping',
        {"lon": lng, "lat": lat})

    if loc_json.get('status') != 200:
        error_message = 'error posting location! %s: %s' % (
            loc_json.get('status'), loc_json.get('error'))
        raise TinderApiError(error_message)


def get_records():
    recs_json = _make_api_call(
        'POST',
        '/user/recs',
        {"limit": max_records_per_request},
    )

    if 'message' in recs_json:
        raise TinderApiError('error getting recs: %s' % recs_json['message'])

    status = recs_json.get('status')
    if status != 200:
        raise TinderApiError('error getting recs: %s' % status)

    return recs_json.get('results', [])


def like(record_id):
    like_json = _make_api_call(
        'GET',
        '/like/%s' % record_id,
    )

    return like_json


def send_message(match_id, message):
    _make_api_call(
        'POST',
        '/user/matches/%s' % match_id,
        {'message': message},
    )


def get_updates(timestamp):
    updates_json = _make_api_call(
        'POST',
        '/updates',
        {"last_activity_date": timestamp},
    )

    return updates_json


def get_match_info(match_id):
    """
    no idea if this actually works
    """
    match_json = _make_api_call(
        'GET',
        '/user/matches/%s' % match_id,
    )

    return match_json