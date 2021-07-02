# instagram-scraper

DOES NOT WORK CURRENTLY! NEEDS WORK...
  
Originaly there were a init.py, start.py. pictures.py... This is now all within enhanced..py 

This is a simple script that starts with a given user (set the startpoint with init.py) and scraps all of his followers in start.py;

once it has a few users you can run pictures.py to scrape data from posts (infos like location and who tagged who)

Now this means you continue reading and check out how it is working in the moment

# How to use?
0. Install python, pip and arangoDB on your machine and download the repo
1. Run ```pip3 install -r requirements.txt```
2. Then run enhanced..py --> This includes mostly everything now. You will be asked to enter your private login data and more like db-config. Check out the generated json if you want more control. If you want to add more insta accounts for public scanning you must create a file accounts.json and add a list of dictionaries meaning [{'email':'...', 'password':'...'},{},{},..]
3. Read the readme to the end. Then run the EnhancedUserScanScript.py script several times --> This will scrap your followers, the posts of each scraped user, the location of each post, the people tagged in it and the hashtags. It might be, that you have to make additional statements in the code so it works best for you. Learn more by continuing reading the readme.

# How does it work?
We are using [igramscraper](https://github.com/realsirjoe/instagram-scraper.git) to authenticate to the instagram api and fetch all the data.
The entrypoint usually is your login username, but you can change this in the arangodb web panel by altering the initialized username.
running the start.py script takes all usernames in your database and fetches all the profiles following that user.
Afterward it creates a new entry for that newly found user and creates the follows relationship between the two users.
by rerunning this script all the newly found users are now also scraped.

# Current practices
According to the 19.04.2020 the script has changed very often. At least you have to read the code and understand it particualry. The script enhanced..py contains all the main functions. Main is at the bottom. The current practice is: You got 1 private account (your own) and maybe you got some others which you can use to scan public profiles. So this script comes with multithreading. When multithreading there is one thread putting jobs into specific queues (relationScanner (follow(er)s) and postsScanner). The two public workers - relationScanner and postsScanner take the information from their queue and do their job. Due to rate limits by insta we got to hook the requests session from [igramscraper](https://github.com/realsirjoe/instagram-scraper.git) to count pending requests and limit them by time.sleep or exit() the thread. So differentiate bitween public and private scanner. This decides how you initialize the customInsta class. Check it out within the code. Another very important main practice is that we decide per aql-arango-query-language wich users shall be scanned. Of course there are some other limiters in the code like 'dont scan users with more than 5K follows'. So read the arango documentation, learn a bit aql and check out in the code where it is used. Always try your aql within the db-web-interface to see if it works. Than copy into the code, adapt and run.
