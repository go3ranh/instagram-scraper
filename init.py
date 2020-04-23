from igramscraper.instagram import Instagram
import time
import os
from arango import ArangoClient
import configsystem
import TimeHack

TimeHack.Hack()

config = configsystem.load()

client = ArangoClient()
db = client.db(config['DB_name'], config['DB_username'], config['DB_password'])

if db.has_graph("users"):
    usersGraph = db.graph("users")
else:
    usersGraph = db.create_graph("users")

if not usersGraph.has_vertex_collection("users"):
    usersGraph.create_vertex_collection("users")

users = usersGraph.vertex_collection('users')

if not users.has(config['Instagram_username']):
    users.insert({
        "_key": config['Instagram_username'],
        "username": config['Instagram_username'],
        "id": "",
        "fullName": "",
        "biography": "",
        "profilePicture": "",
        "externalUrl": '',
        "numPosts": 0,
        "isPrivate": True
    })
