import requests
import os

from src import STATIC_PATH


def flickr_request(query):
    url = 'https://api.flickr.com/services/rest/'
    api_key = os.environ.get('API_KEY', '')
    params = {'api_key': '55967ec1dcab1572d9c16f3f807721b7', 'text': query, \
              'privacy_filter': 1, 'license': 3, 'content_type': 1, 'format': 'json', 'per_page': 1,
              "method": "flickr.photos.search", 'nojsoncallback': 1}
    request = requests.get(url, params=params)
    return request.json()


def check_for_image(query):
    """Recursive"""
    query = query.strip().lower()
    word = query.replace(' ', '_') + '.jpg'
    file_list = os.listdir(os.path.join(STATIC_PATH, 'img'))
    if word in file_list:
        print('Image found in database')
        path = 'img/' + word
        return path
    else:
        if build_url(flickr_request(query), word):
            return check_for_image(query)
        return "img/nothing_to_display.jpg"


def build_url(params, word):
    try:
        server_id = params['photos']['photo'][0]['server']
        id = params['photos']['photo'][0]['id']
        secret = params['photos']['photo'][0]['secret']
    except (IndexError, KeyError):
        return False
    else:
        url = f'https://live.staticflickr.com/{server_id}/{id}_{secret}.jpg'
        print('Adding image to database')
        write_image(url, word)
        return url

#ADD SECURE FILENAM
def write_image(url, query):
    request = requests.get(url)
    filename = os.path.join(STATIC_PATH, 'img', query)
    with open(filename, 'wb') as file:
        file.write(request.content)
