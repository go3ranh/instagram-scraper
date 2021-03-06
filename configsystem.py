import json

# Here all the preconfig and default values goes.
# Make new line and add your settings as you recognize the pattern
# Should be understandable
sample = { 
    "Instagram_username": {"Message": "Please enter your Instagram username", "Value": None} ,
    "Instagram_email": {"Message": "Please enter your Instagram emailaddress (or username again)", "Value": None},
    "Instagram_password": {"Message": "Please enter your Instagram password", "Value": None},
    "DB_username": {"Message": "Please enter your arango DB username", "Value": None},
    "DB_password": {"Message": "Please enter your arango DB password", "Value": None},
    "DB_name": {"Message": "Please enter your arango DB database-name", "Value": None},
    "PostScannersCount": {"Message": "How many workers shall scan for posts", "Value": 2},
    "RelationScannersCount": {"Message": "How many workers shall scan relations", "Value": 2},
    
}


# Load settigns from file
def load():
    res = None
    global sample 
    try:
        # What does this
        # 1. opens file and loads data
        # 2. than it checks if all values from sample are existing
        # 3. If they are missing but there is a default value, use the default value
        # 4. If not, ask the user
        with open("config.json", "r") as f:
            res = json.load(f)
            Change = False
            for key in sample:
                if res.get(key) == None:
                    Change = True
                    if sample[key]['Value'] == None:
                        res[key] = input(sample[key]['Message'] + ": ")
                    else:
                        res[key] = sample[key]['Value']
                elif res[key] == None:
                    Change = True
                    if sample[key]['Value'] == None:
                        res[key] = input(sample[key]['Message'] + ": ")
                    else:
                        res[key] = sample[key]['Value']
            if Change:
                save(res)
    except IOError:
        print("No config file was found!")
        res = guidedInput()
    return res

# Does somehow the same like load()
def guidedInput():
    res = {}

    global sample
    for key in sample:
        if sample[key]['Value'] == None:
            res[key] = input(sample[key]['Message'] + ": ")
        else:
            res[key] = sample[key]['Value']
    save(res)
    return res

def save(values):
    try:
        with open("config.json", "w") as f:
            json.dump(values, f)
    except IOError:
        print("Couldnt save config file")
