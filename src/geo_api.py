import datetime
import os
import sqlite3

import requests
from flask import session, request

from src import db, DATA_PATH
from src.models import Tracker


def geo_request():

    def ip_tracker():
        """This part is intentionally added for Heroku"""
        response = request.headers.get('X-Forwarded-For', '')
        print('This is the real clients ip address --------', response)
        session['ip'] = response
        return response

    ip_address = ip_tracker()
    if ip_address:
        url = 'http://ipwho.is/'
        _request = requests.get(url + ip_address)
        return _request.json()
    return False


def make_response_geo_data(json_response, route):
    if not json_response:
        tracker = Tracker(ipaddress='Unknown', city='Unknown', country='Unknown')
        db.session.add(tracker)
        db.session.commit()
        print('Could not track user location')
    else:
        session['city'] = json_response["city"]
        session['country'] = json_response["country"]
        session['flag'] = json_response["flag"]["emoji"]
        session['datetime'] = datetime.datetime.now().strftime('%d-%b-%Y, %H:%M:%S')
        ipaddress = json_response.get('ip', 'Unknown')
        city = json_response.get('city', 'Unknown')
        country = json_response.get('country', 'Unknown')
        tracker = Tracker(ipaddress=ipaddress, city=city, country=country, action=route)
        db.session.add(tracker)
        db.session.commit()
        print('Tracker added...')
        return 'success'


def return_unique_visitors():
    try:
        db = sqlite3.connect(os.path.join(DATA_PATH, 'cook.db'))
        count = db.execute('SELECT COUNT(DISTINCT ipaddress) FROM iptracker').fetchone()
        print(count)
    except (FileNotFoundError, sqlite3.DatabaseError):
        return False
    else:
        db.close()
        return count[0]
