import requests
from Utils.Colors import debug
def get_cookie() -> dict:
    debug('Get cookie for google')   
    r = requests.get('https://www.google.com')
    return r.cookies.get_dict()