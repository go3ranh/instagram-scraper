
from arango import ArangoClient
import configsystem
import re
import hashlib

config = configsystem.load()
client = ArangoClient()
db = client.db(config['DB_name'], config['DB_username'], config['DB_password'])


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

while True:
    aql = 'for post in posted let ref = first(for p in posts filter p._id == post._to return p) let ref1 = first(for u in users filter u._id == post._from return u) filter contains(ref.caption,"#") LIMIT 1000 return merge(post,ref,ref1)'
    res = db.aql.execute(aql)

    if len(res.batch()) == 0:
        break

    for media in res.batch():
        matches = re.findall("#\s?(\w+)", media['caption'])
        for match in matches:
            #match = match.group(1)
            #print('[%s] Hashtag found: %s' % (media['username'],match))

            HMatch = hashlib.sha1(match.encode()).hexdigest()
            entry = {
                '_key':HMatch,
                'value':match
            }
            if not hashtags.has(entry):
                hashtags.insert(entry)


            entry = {
                '_key': media['username'] + "-" + HMatch,
                '_from':'users/' + media['username'],
                '_to':'hashtags/'+HMatch
            }
            if not usedHashtags.has(entry):
                usedHashtags.insert(entry)

print('All hashtags indexed :)')