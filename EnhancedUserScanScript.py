import proxies
import time
from arango import ArangoClient
import configsystem
import random
from igramscraper.instagram import Instagram
from queue import Queue
from threading import Thread
from threading import Lock
import requests
import json
import re
import hashlib

config = configsystem.load()
client = ArangoClient()
db = client.db(config['DB_name'], config['DB_username'], config['DB_password'])
queueRelations = Queue()
queuePosts = Queue()

StandardSleepTime = 0.1


# region SetupDatabase



if db.has_graph("users"):
    usersGraph = db.graph("users")
else:
    usersGraph = db.create_graph("users")

if not usersGraph.has_vertex_collection("users"):
    usersGraph.create_vertex_collection("users")
if not usersGraph.has_vertex_collection("locations"):
    usersGraph.create_vertex_collection("locations")
if not usersGraph.has_vertex_collection("posts"):
    usersGraph.create_vertex_collection("posts")
if not usersGraph.has_vertex_collection("hashtags"):
    usersGraph.create_vertex_collection("hashtags")

if not usersGraph.has_edge_collection("usedHashtags"):
    usedHashtags = usersGraph.create_edge_definition(
        edge_collection="usedHashtags",
        from_vertex_collections=['users'],
        to_vertex_collections=['hashtags']
    )

if not usersGraph.has_edge_collection("follows"):
    follows = usersGraph.create_edge_definition(
        edge_collection="follows",
        from_vertex_collections=['users'],
        to_vertex_collections=['users']
    )

if not usersGraph.has_edge_collection('wasAt'):
    wasAt = usersGraph.create_edge_definition(
        edge_collection='wasAt',
        from_vertex_collections=['users'],
        to_vertex_collections=['locations']
    )
if not usersGraph.has_edge_collection('posted'):
    posted = usersGraph.create_edge_definition(
        edge_collection='posted',
        from_vertex_collections=['users'],
        to_vertex_collections=['posts']
    )
if not usersGraph.has_edge_collection('tagged'):
    tagged = usersGraph.create_edge_definition(
        edge_collection='tagged',
        from_vertex_collections=['posts'],
        to_vertex_collections=['users']
    )

# endregion

# region loadDB
users = usersGraph.vertex_collection('users')
locations = usersGraph.vertex_collection('locations')
follows = usersGraph.edge_collection('follows')
wasAt = usersGraph.edge_collection('wasAt')
posts = usersGraph.vertex_collection('posts')
posted = usersGraph.edge_collection('posted')
tagged = usersGraph.edge_collection('tagged')
hashtags = usersGraph.vertex_collection('hashtags')
usedHashtags = usersGraph.edge_collection('usedHashtags')
# endregion

def getRandomProxy():
    proxy = random.choice(proxies.get_proxies())
    if proxy:
        proxy = {'http': 'http://%s:%s'%(proxy['IP'], proxy['PORT'])}
        return proxy
    else:
        return False


allCredentials = []
freeCredentials = allCredentials
def getRandomFreeCredentials():
    if freeCredentials:
        credit = freeCredentials[0]
        freeCredentials.remove(credit)
        return credit
    else:
        return False

def returnCredential(credit):
    freeCredentials.append(credit)

def loadCredentials():
    global allCredentials
    global freeCredentials
    try:
        with open('accounts.json', 'r') as r:
            allCredentials = json.load(r)
            freeCredentials = allCredentials
    except:
       print("Couldn not load credentials")

def testProxy(proxy):
    try:
        s = requests.session()
        s.proxies = proxy
        s.verify = True
        res = s.get('https://www.instagram.com/' )
        return True
    except:
        return False


class customInstagram(Instagram):

    def __init__(self, useProxy = True, autoRotate = True, maxRequestcount = 120, logindata = None):
        # Initialize
        # Gonna set some vars for statistics, login and proxy management
        # But rotating logins and proxys doesnt work well in the momen so it is not really used 
        self.useProxy = True
        self.overallRequestCount = 0
        self.ready = False
        self.currentCredit = None
        self.logindata = logindata
        self.autoRotate = autoRotate
        self.maxRequestCount = maxRequestcount
        Instagram.__init__(self, 1.3) # second arg is standard sleep after each req 
        self.parent = super(customInstagram, self) # Link to superclass, dont want to write super ... all the time
        self.Auth() # login and proxy selection

        # Inject Hook
        self.oldReqGet = self._Instagram__req.get #_...___ receives hidden var from super class... req = session, we will path get function in order to count requests and add additonal limits time/maxcount 
        self._Instagram__req.verify = True
        self._Instagram__req.get = self.hookedRequest
        self.requestCount = 0

    def Auth(self):
        Instagram.__init__(self, 0.1)

        if self.useProxy:
            if not self.RotateProxy():
                self.ready = False
                return
        #logindata means the user has provided specific credentials - it is for the private account
        if not self.logindata:
            if not self.tryLogin():
                self.ready = False
                return
            self.ready = True
        else:
            self.with_credentials(self.logindata[0],self.logindata[1])
            try:
                self.login()
                self.ready = True
            except:
                self.ready = False

    def tryLogin(self):
        LoggedInSuccessful = False
        # Try to find valid credentials as long as there are any
        while not LoggedInSuccessful and len(freeCredentials)>0:
            # This line is because rotation works not that well and I dont want to change logged in user... But if you want to rotate, remove the if block
            if self.currentCredit:
                self.with_credentials(self.currentCredit['email'], self.currentCredit['password'])
                try:
                    self.login()
                    LoggedInSuccessful = True
                    print("Successfuly logged in with: " + self.currentCredit['email'])
                    return True
                except:
                    pass
            credit = getRandomFreeCredentials()
            if credit:
                self.with_credentials(credit['email'], credit['password'])
                try:
                    self.login()
                    LoggedInSuccessful = True
                    self.currentCredit = credit
                    print("Successfuly logged in with: " + credit['email'])
                    return True
                except:
                    pass
        if not LoggedInSuccessful:
            print("No credentials could login...")
            return False

    def RotateProxy(self):
        proxy = getRandomProxy()
        tests = 0
        while not (testProxy(proxy)) and tests < 10:
            tests += 1
            proxy = getRandomProxy()
        if tests < 10:
            self.parent.set_proxies(proxy)
            return True
        else:
            print("Couldn't conenct to any proxy after 10 tries... :/")
            return False

    def returnCredit(self):
        if self.currentCredit:
            returnCredential(self.currentCredit)
            self.currentCredit = None


    def hookedRequest(self,url, **kwargs):

        # Some disabled rotation stuff...

        # if self.autoRotate and not self.logindata and (self.requestCount > self.maxRequestCount):
        #     time.sleep(60)
        #     self.requestCount = 0
        #     self.Auth()

        # if self.autoRotate and self.logindata and (self.requestCount > self.maxRequestCount):
        #     self.ready = False
        #     print("Max amount of requests reached for private account")
        #     return


        # ready means the class is allowed to start its work
        if self.ready:
            # load request from hook backup and check if rate limit error, else return otherwise exit thread because account is dead for one day and we dont want to continue with that.
            # Seems to be better to not exceed rate limit, then it seems like user can do more requests
            result = self.oldReqGet(url, **kwargs)
            if result.status_code == 429:
                print('[%s] was blocked after [%i requests] and will exit now.' % (self.session_username, self.requestCount))
                exit(0)

            # Some counting...
            self.requestCount += 1
            self.overallRequestCount +=1
            # Here would go autorotate...

            # Show status
            #if self.overallRequestCount % 10 == 0:
            print('[%i of %i | %i requests] [%s]' % (self.requestCount ,self.maxRequestCount,self.overallRequestCount, self.session_username))


            # here goes some temp limiting
            if self.overallRequestCount % 10 == 0:
                time.sleep(5)
            if self.overallRequestCount % 50 == 0:
                time.sleep(20)
            if self.overallRequestCount % 70 == 0:
                exit(0)
            if self.overallRequestCount % 100 == 0:
                time.sleep(60)



            return result
        else:
            # Kills thread
            print('[%s] tried to make a request before beeing ready. Thread will stop now.'%(self.session_username))
            exit(0)

def updateAccount(acc):
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
        users.update({
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
        })



def scanFollows(profile, insta):
    print("[users: %i] [%s] Scanning follows of: %s" % (users.count(),insta.session_username,profile.get('username')))
    try:
        account = insta.get_account(profile.get('username'))
    except:
        return
    updateAccount(account)

    if account.follows_count > 5000:
        return

    if account.follows_count > 10:
        following = insta.get_following(
            account.identifier, account.follows_count, 10, delayed=True)
    else:
        following = insta.get_following(
            account.identifier, account.follows_count, account.follows_count, delayed=True)
    if following:
        for follow in following['accounts']:
            updateAccount(follow)
            # edges erstellen
            if not follows.has(account.username + '-' + follow.username):
                follows.insert({
                    '_key': account.username + '-' + follow.username,
                    '_from': 'users/' + account.username,
                    '_to': 'users/' + follow.username
                })
    pass


def scanFollowers(profile, insta):
    print("[users: %i] [%s] Scanning followers of: %s" % (users.count(),insta.session_username,profile.get('username')))

    try:
        account = insta.get_account(profile.get('username'))
    except:
        return
    updateAccount(account)

    if account.followed_by_count > 5000:
        return

    if account.followed_by_count > 10:
        followers = insta.get_followers(
            account.identifier, account.followed_by_count, 10, delayed=True)
    else:
        followers = insta.get_followers(
            account.identifier, account.followed_by_count, account.followed_by_count, delayed=True)
    if followers:
        for follower in followers['accounts']:
            updateAccount(follower)
            # edges erstellen
            if not follows.has(follower.username + '-' + account.username):
                follows.insert({
                    '_key': follower.username + '-' + account.username,
                    '_from': 'users/' + follower.username,
                    '_to': 'users/' + account.username
                })

    pass


def scanPosts(profile, insta):
    print("[users: %i] [%s] Scanning posts of: %s" % (users.count(),insta.session_username, profile.get('username')))
    try:
        account = insta.get_account(profile.get('username'))
    except:
        return
    
    updateAccount(account)

    if account.media_count > 200:
        return

    if account.media_count == 0:
        return


    medias = insta.get_medias_by_user_id(account.identifier, account.media_count)

    counter = 0
    for media in medias:
        counter += 1
        if posts.has(media.identifier):
            continue

        # need to be loaded again for gettin locations
        media = insta.get_media_by_url(media.link)
        print('[%s] [%s] [%i of %i] [@ %s]' % (insta.session_username,account.username, counter, len(medias), media.location_name))
    
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
                updateAccount(acc)
            
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
                    updateAccount(acc)
                if not wasAt.has(uName+ '-' + media.location_slug):
                    wasAt.insert({
                        '_key': uName + '-' + media.location_slug,
                        '_from': 'users/' + uName,
                        '_to': 'locations/' + media.location_slug
                    })
    


def WorkerScanPosts(q):
    insta = customInstagram()
    while True:
        if insta.ready:
            if not q.empty():
                profile = q.get()
                if profile is None:
                    exit(0)
                    break
                # Do Work
                if not profile.get('isPrivate'):
                    if profile.get('numPosts') == None or profile.get('numPosts') < 200:
                        scanPosts(profile,  insta)
                    profile['lastScanPosts'] = time.time()
                    profile = users.get({'_key': profile['_key']})
                    users.update(profile)
            else:
                time.sleep(0.1)
        else:
            print("Could not get Instagram client... :/")
            exit(0)
            break    

def WorkerScanRelation(q):
    insta = customInstagram()
    while True:
        if insta.ready:
            if not q.empty():
            
                profile = q.get()
                if profile is None:
                    exit(0)
                    break
                # Do Work
                if not profile.get('isPrivate'):
                    if profile.get('numFollowers') == None or profile.get('numFollowers') < 5000:
                        scanFollowers(profile,  insta)
                    if profile.get('numFollows') == None or profile.get('numFollows') < 5000:
                        scanFollows(profile, insta)
                    profile['lastScan'] = time.time()
                    profile = users.get({'_key': profile['_key']})
                    users.update(profile)
            else:
                time.sleep(0.1)
        else:
            print("Could not get Instagram client... :/")
            exit(0)
            break    

stopManager = False
def JobManager():
    while stopManager == False:
        deads = 0
        for t in threads:
            if not t.is_alive():
                deads+=1
        if len(threads)-1 == deads:
            exit(0)
        if queueRelations.empty():
            aql = 'FOR user in 1..2 ANY @source GRAPH "users" filter user.isPrivate == false filter user.lastScan == null LIMIT 100 return user '
            res = db.aql.execute(aql, bind_vars={'source':'users/'+config['Instagram_username']})
            for profile in res.batch():
                queueRelations.put(profile)
        if queuePosts.empty():
            aql = 'for u in inbound CONCAT("users/",@source) graph "users" prune u.lastScanPosts == null OPTIONS {bfs:True} filter u.lastScanPosts == null filter u.isPrivate == false filter u.numPosts <= @lim LIMIT 20 return u'
            res = db.aql.execute(aql, bind_vars={'lim':200,'source': config['Instagram_username']})
            for profile in res.batch():
                queuePosts.put(profile)
        time.sleep(1)


threads = []


RelationScannerCount = config['RelationScannersCount']
PostScannerCount = config['PostScannersCount']

def StartWork():
    for i in range(RelationScannerCount):
        t = Thread(target=WorkerScanRelation,name="[R-%i] Relation Scanner"%i, args=(queueRelations,))
        t.start()
        threads.append(t)
    for i in range(PostScannerCount):
        t = Thread(target=WorkerScanPosts, name = "[P-%i] Post Scanner"%i,args=(queuePosts,))
        threads.append(t)
        t.start()
    t = Thread(target=JobManager, name= "Job Manager")
    threads.append(t)    
    t.start()


def StopWork():
    queueRelations.join()
    [queueRelations.put(None) for i in range(RelationScannerCount)]

    queuePosts.join()
    [queuePosts.put(None) for i in range(PostScannerCount)]

    [t.join for t in threads]




def initAccount(seq):
    usr, pw = seq
    instagram = Instagram(StandardSleepTime)
    instagram.with_credentials(usr, pw)
    try:
        instagram.login()
        print("Login successful with %s" % (usr))
        return instagram
    except Exception as e:
        print("Could not login: %s. Error: %s" % (usr, str(e)))
        return None




if not users.has(config['Instagram_username']):
    users.insert({
        "_key": config['Instagram_username'],
        "username": config['Instagram_username'],
        "isPrivate": True
    })





loadCredentials()
privateInsta = customInstagram(useProxy=False, autoRotate=False,maxRequestcount=200, logindata=(config['Instagram_email'], config['Instagram_password']))
StartWork()


    # Do private jobs


# (Fist of all the db has to work)

# What you have to do
# 1. Check aqls in bellow and scannerworkers so you can adapt them to your needs. Test them in the db
# 2. Set worker counts in config json... (Maybe you only want to scan posts) make sure enough working account are in accoutns.json. 
# 3. Disable blocks by comments if you do not need the functionality
# 4. Check customInstagram --> Hook function --> There are sleep times and exit conditions based on your request count
# GO

if privateInsta.ready:
    try:
        # Get users for normal scan



        #Scan relations
        aql = 'for user in 1 outbound @source follows filter user.isPrivate == True filter user.lastScan == null return user'
        res = db.aql.execute(aql, bind_vars={'source':'users/'+config['Instagram_username']})
        for profile in res.batch():
            #process
            if privateInsta.ready:
                scanFollowers(profile,privateInsta)
                scanFollows(profile, privateInsta)
                profile = users.get({'_key': profile['_key']})
                profile['lastScan'] = time.time()
                users.update(profile)


        #Scan posts
        aql = 'for user in 1 outbound @source follows filter user.isPrivate == True filter user.lastScanPosts == null return user'
        res = db.aql.execute(aql, bind_vars={'source':'users/'+config['Instagram_username']})


        for profile in res.batch():
            #process
            if privateInsta.ready:
                scanPosts(profile, privateInsta)
                profile = users.get({'_key': profile['_key']})
                profile['lastScanPosts'] = time.time()
                users.update(profile)
                time.sleep(10)
    except:
        pass


print("Main thread has finished. Kill program if you want to stop.")








#StopWork()
[t.join() for t in threads]




