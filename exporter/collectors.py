import hashlib
import re
import time
from .database import *
from igramscraper.instagram import Instagram


def collect_follows(username, insta: Instagram, bypass = False):
    print("[users: %i] Scanning follows of: %s" % (users.count(), username))
    account = insta.get_account(username)

    if account.follows_count > 1000 and bypass == False:
        return


    following = insta.get_following(
        account.identifier, account.follows_count, account.follows_count, delayed=True)

    if following:
        for follow in following['accounts']:
            update_account(follow)
            # edges erstellen
            if not follows.has(account.username + '-' + follow.username):
                follows.insert({
                    '_key': account.username + '-' + follow.username,
                    '_from': 'users/' + account.username,
                    '_to': 'users/' + follow.username
                })


def collect_followers(username, insta: Instagram, bypass = False):
    print("[users: %i] Scanning followers of: %s" % (users.count(), username))
    account = insta.get_account(username)

    update_account(account)

    if account.followed_by_count > 1000 and bypass == False:
        return


    followers = insta.get_followers(
        account.identifier, account.followed_by_count,account.followed_by_count, delayed=True)
    if followers:
        for follower in followers['accounts']:
            update_account(follower)
            if not follows.has(follower.username + '-' + account.username):
                follows.insert({
                    '_key': follower.username + '-' + account.username,
                    '_from': 'users/' + follower.username,
                    '_to': 'users/' + account.username
                })


def collect_posts(username, insta: Instagram):
    print("[users: %i] Scanning posts of: %s" % (users.count(), username))
    account = insta.get_account(username)
    update_account(account)
    profile = users.get(username)
    
    ammount  = 200 if account.media_count > 200 else account._media_count
    
    medias = insta.get_medias_by_user_id(account.identifier, ammount)

    counter = 0
    for media in medias:
        counter += 1
        if posts.has(media.identifier):
            continue

        # need to be loaded again for gettin locations
        media = insta.get_media_by_url(media.link)
        print(' [%s] [%i of %i] [@ %s]' % (account.username, counter, len(medias), media.location_name))
    
        if not posts.has(media.identifier):
            posts.insert({
                '_key': media.identifier,
                'locationSlug': media.location_slug,
                'locationName': media.location_name,
                'caption': media.caption,
                'createdTime': media.created_time,
                'countComents': media.comments_count,
                'coments': media.comments,
                'link': media.link,
                'mediaCode': media.get_code_from_id(media.identifier)
            })
        if not posted.has(account.username + '-' + media.identifier):
            posted.insert({
                '_key': account.username + '-' + media.identifier,
                '_from': profile.get('_id'),
                '_to': 'posts/' + media.identifier
            })


        
        # Hashtag scan goes here
        if media.caption:
            matches = re.findall("#\s?(\w+)", media.caption)
            for match in matches:
                #match = match.group(1)
                print('Hashtag found: %s' % match)

                HMatch = hashlib.sha1(match.encode()).hexdigest()
                entry = {
                    '_key':HMatch,
                    'value':match
                }
                if not hashtags.has(entry):
                    hashtags.insert(entry)


                entry = {
                    '_key': account.username + "-" + HMatch,
                    '_from':'users/' + account.username,
                    '_to':'hashtags/'+HMatch
                }
                if not usedHashtags.has(entry):
                    usedHashtags.insert(entry)




        time.sleep(1)
        taggedUsers = insta.get_media_tagged_users_by_code(
            media.short_code)
        for user in taggedUsers:
            uName = user.get('user').get('username')
            if not users.has({'_key':uName}):
                acc = insta.get_account(user.get('user').get('username'))
                update_account(acc)
            
            if not tagged.has(account.username + '-' + uName + '-' + media.identifier):
                tagged.insert({
                    '_key': account.username + '-' + uName + '-' + media.identifier,
                    '_from': 'posts/' + media.identifier,
                    '_to': 'users/' + uName
                })

        if media.location_name != None:
            if not locations.has(media.location_slug):
                location = insta.get_location_by_id(media.location_id)
                locations.insert({
                    '_key': media.location_slug,
                    'id': media.location_id,
                    'name': media.location_name,
                    'long': location.lng,
                    'lat': location.lat
                })
            if not wasAt.has(account.username + '-' + media.location_slug):
                wasAt.insert({
                    '_key': account.username + '-' + media.location_slug,
                    '_from': 'users/' + account.username,
                    '_to': 'locations/' + media.location_slug
                })
            for user in taggedUsers:
                uName = user.get('user').get('username')
                # This should actually never happen because all useres are iterated above and so should this one be included... Be removal we could save server requests to our own db
                if not users.has({'_key': uName}):
                    acc = insta.get_account(
                        user.get('user').get('username'))
                    update_account(acc)
                if not wasAt.has(uName+ '-' + media.location_slug):
                    wasAt.insert({
                        '_key': uName + '-' + media.location_slug,
                        '_from': 'users/' + uName,
                        '_to': 'locations/' + media.location_slug
                    })





def update_account(acc):
    """
    Creates or updates a user in the db.
    """


    print('Updating account: %s' % acc.username)
    if not users.has(acc.username):
        users.insert({
            '_key': acc.username,
            'username': acc.username,
            'id': acc.identifier,
            'fullName': acc.full_name,
            'biography': acc.biography,
            'profilePicture': acc.get_profile_picture_url(),
            'externalUrl': acc.external_url,
            'numPosts': acc.media_count,
            'numFollowers': acc.followed_by_count,
            'numFollows': acc.follows_count,
            'isPrivate': acc.is_private,
            'lastScan': None,
            'lastScanPosts': None
        })
    else:

        # ! Updating is a bit buggy. Not fully initialized user objects from insta api can overwrite existing things with 0 or null
        user = users.get(acc.username)
        users.update({
            '_key': acc.username,
            'fullName': acc.full_name if acc.full_name is not None else user['fullName'],
            'biography': acc.biography if acc.biography is not None else user['biography'],
            'profilePicture': acc.get_profile_picture_url() if acc.get_profile_picture_url() is not None else user['profilePicture'],
            'externalUrl': acc.external_url if acc.external_url is not None else user['externalUrl'],
            'numPosts': acc.media_count if acc.media_count > 0 else user['numPosts'],
            'numFollowers': acc.followed_by_count if acc.followed_by_count > 0 else user['numFollowers'],
            'numFollows': acc.follows_count if acc.follows_count > 0 else user['numFollows'],
            'isPrivate': acc.is_private
        })
