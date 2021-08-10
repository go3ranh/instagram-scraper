# instagram-scraper

## About

...

## How to use
- Create a virtual python environment and activate it
- Install requirements via `pip install -r requirements.txt`
  - If this does not work clone https://github.com/realsirjoe/instagram-scraper. Navigate to the dir. Install requirements. Run `python setup.py install`
- You need to setup an arangodb. Create a database and a user.
- Configuration will be requested by the app via console input

## Annotations
- The `main.py` is bloated with some debug and dev stuff.


## Unittest

Authenticated unittests of https://github.com/realsirjoe/instagram-scrape

:rotating_light: This means that anything about locations is not usable rightnow and needs to be fixed or requires a workaround.

```
......EEE..E.E...
======================================================================
ERROR: test_get_location_by_id (__main__.TestIgramscraper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\tests\test_igramscraper.py", line 79, in test_get_location_by_id
    location = self.instagram.get_location_by_id(1)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 815, in get_location_by_id
    return Location(json_response['graphql']['location'])
TypeError: 'NoneType' object is not subscriptable

======================================================================
ERROR: test_get_location_medias_by_id (__main__.TestIgramscraper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\tests\test_igramscraper.py", line 75, in test_get_location_medias_by_id    
    medias = self.instagram.get_medias_by_location_id(1, 56)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 600, in get_medias_by_location_id
    nodes = arr['graphql']['location']['edge_location_to_media'][
TypeError: 'NoneType' object is not subscriptable

======================================================================
ERROR: test_get_location_top_medias_by_id (__main__.TestIgramscraper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\tests\test_igramscraper.py", line 71, in test_get_location_top_medias_by_id
    medias = self.instagram.get_current_top_medias_by_tag_name(1)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 645, in get_current_top_medias_by_tag_name
    json_response['graphql']['hashtag']['edge_hashtag_to_top_posts'][
KeyError: 'graphql'

======================================================================
ERROR: test_get_medias (__main__.TestIgramscraper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\tests\test_igramscraper.py", line 44, in test_get_medias
    medias = self.instagram.get_medias('kevin', 80)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 298, in get_medias
    account = self.get_account(username)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 1255, in get_account
    if user_array['entry_data']['ProfilePage'][0]['graphql']['user'] is None:
KeyError: 'ProfilePage'

======================================================================
ERROR: test_get_medias_by_tag (__main__.TestIgramscraper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\tests\test_igramscraper.py", line 52, in test_get_medias_by_tag
    medias = self.instagram.get_medias_by_tag('youneverknow', 20)
  File "g:\instagram-scraper\venv\Lib\site-packages\igramscraper-0.3.5-py3.9.egg\igramscraper\instagram.py", line 536, in get_medias_by_tag
    raise InstagramException.default(response.text,
igramscraper.exception.instagram_exception.InstagramException: Response code is 560. Body:  Something went wrong. Please report issue., Code:560

----------------------------------------------------------------------
Ran 17 tests in 24.385s

FAILED (errors=5)
```
