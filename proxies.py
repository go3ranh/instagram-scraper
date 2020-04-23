import requests
from lxml.html import fromstring
import json

def get_proxies():
    res = requests.get("https://www.proxy-list.download/api/v0/get?l=en&t=http")
    httpsProxies = None
    if res.ok:
        httpsProxies = json.loads(res.content)

    CountryFilter = ['Germany']
    #CountryFilter = ['Germany']
    AnnonymityFilter = ['Elite', 'Anonymous']
    httpsProxies = [d for d in httpsProxies[0]['LISTA'] if d['COUNTRY'] in CountryFilter and d['ANON'] in AnnonymityFilter]

    return httpsProxies
