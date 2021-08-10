from arango import ArangoClient

from . import configsystem

_config = configsystem.load()
db = ArangoClient().db(_config['DB_name'], _config['DB_username'], _config['DB_password'])

if db.has_graph("users"):
    _usersGraph = db.graph("users")
else:
    _usersGraph = db.create_graph("users")

if not _usersGraph.has_vertex_collection("users"):
    _usersGraph.create_vertex_collection("users")
if not _usersGraph.has_vertex_collection("locations"):
    _usersGraph.create_vertex_collection("locations")
if not _usersGraph.has_vertex_collection("posts"):
    _usersGraph.create_vertex_collection("posts")
if not _usersGraph.has_vertex_collection("hashtags"):
    _usersGraph.create_vertex_collection("hashtags")

if not _usersGraph.has_edge_collection("usedHashtags"):
    usedHashtags = _usersGraph.create_edge_definition(
        edge_collection="usedHashtags",
        from_vertex_collections=['users'],
        to_vertex_collections=['hashtags']
    )

if not _usersGraph.has_edge_collection("follows"):
    follows = _usersGraph.create_edge_definition(
        edge_collection="follows",
        from_vertex_collections=['users'],
        to_vertex_collections=['users']
    )

if not _usersGraph.has_edge_collection('wasAt'):
    wasAt = _usersGraph.create_edge_definition(
        edge_collection='wasAt',
        from_vertex_collections=['users'],
        to_vertex_collections=['locations']
    )
if not _usersGraph.has_edge_collection('posted'):
    posted = _usersGraph.create_edge_definition(
        edge_collection='posted',
        from_vertex_collections=['users'],
        to_vertex_collections=['posts']
    )
if not _usersGraph.has_edge_collection('tagged'):
    tagged = _usersGraph.create_edge_definition(
        edge_collection='tagged',
        from_vertex_collections=['posts'],
        to_vertex_collections=['users']
    )

users = _usersGraph.vertex_collection('users')
locations = _usersGraph.vertex_collection('locations')
follows = _usersGraph.edge_collection('follows')
wasAt = _usersGraph.edge_collection('wasAt')
posts = _usersGraph.vertex_collection('posts')
posted = _usersGraph.edge_collection('posted')
tagged = _usersGraph.edge_collection('tagged')
hashtags = _usersGraph.vertex_collection('hashtags')
usedHashtags = _usersGraph.edge_collection('usedHashtags')

if not users.has(_config['Instagram_username']):
    users.insert({
        "_key": _config['Instagram_username'],
        "username": _config['Instagram_username'],
        "id": "",
        "fullName": "",
        "biography": "",
        "profilePicture": "",
        "externalUrl": '',
        "numPosts": 0,
        "isPrivate": True,
        'lastScan': None,
        'lastScanPosts': None
    })
