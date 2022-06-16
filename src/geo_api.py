import datetime
import sqlite3

import requests
from flask import session

from src import db
from src.models import Tracker


def geo_request():

    def ip_tracker():
        response = requests.get('https://api64.ipify.org?format=json').json()
        result = response.get("ip", None)
        session['ip'] = result
        return result

    ip_address = ip_tracker()
    if ip_address:
        url = 'http://ipwho.is/'
        request = requests.get(url + ip_address)
        return request.json()
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


def return_unique_visitors():
    try:
        db = sqlite3.connect('data/db.sqlite3')
        count = db.execute('SELECT COUNT(DISTINCT ipaddress) FROM iptracker').fetchone()
        print(count)
    except sqlite3.DatabaseError:
        return False
    else:
        db.close()
        return count[0]