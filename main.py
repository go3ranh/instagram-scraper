from igramscraper import instagram
from exporter.database import *
from exporter import configsystem
from exporter import collectors
from igramscraper.instagram import Instagram
from datetime import datetime, timezone
import time
import concurrent.futures

config = configsystem.load()

instagram = Instagram()
instagram.with_credentials(config['Instagram_username'], config['Instagram_password'], '/cache')
instagram.login()
time.sleep(2)

print('instagram login success!')


def scan_user(username):
    collectors.collect_followers(username, instagram)
    collectors.collect_follows(username, instagram)
    set_lastScan(username)


def scan_user_posts(username):
    collectors.collect_posts(username, instagram)
    # set_lastScanPosts(username)


def set_lastScan(username):
    user = users.get(username)
    user['lastScan'] = datetime.now(timezone.utc).timestamp() * 1e3
    users.update(user)


def set_lastScanPosts(username):
    user = users.get(username)
    user['lastScanPosts'] = datetime.now(timezone.utc).timestamp() * 1e3
    users.update(user)


if __name__ == '__main__':

    root_user = users.get(config['Instagram_username'])

    if root_user.get('lastScan') is None:
        collectors.collect_followers(config['Instagram_username'], instagram)
        collectors.collect_follows(config['Instagram_username'], instagram)
        root_user['lastScan'] = datetime.now(timezone.utc).timestamp() * 1e3

        set_lastScan(config['Instagram_username'])

    aql = """
        for u,e,p in inbound @source graph 'users'
            prune u.lastScanPosts == null OPTIONS {bfs:True} 
            filter (u.isPrivate and u in (for user2 in 1 outbound @source follows return user2 )) or u.isPrivate == false
            LIMIT 20
            return u
    """
    res = db.aql.execute(aql, bind_vars={'source': 'users/' + config['Instagram_username']})

    for user in res.batch():
        if user.get('lastScan') is None:
            scan_user_posts(user['username'])
    exit()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for user in res.batch():
            if user.get('lastScan') is None:
                executor.submit(scan_user_posts, user['username'])
