import requests
import sys
import json



def getsinglegeneric(word):


# bn = sys.argv[1]
    if word =="":
        return "not found"

    bn = "brand_name:"+word

    print(bn)

    url = "https://api.fda.gov/drug/ndc.json"

    ##querystring = {"search":"brand_name:%22ADVIL%22","limit":"1"}

    querystring = {"search":bn,"limit":"1"}

    payload = ""
    headers = {
        'cache-control': "no-cache",
        'Postman-Token': "7567d993-8fbd-4606-8dbd-8a4e6525fc93"
        }

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

    ##print(response.text)

    js = json.loads(response.text)

    if "results" in js:
        ##print (js["results"][0]["generic_name"])
        gname = js["results"][0]["generic_name"]
    else:
        gname = "none"

    print(gname)
    return gname

    





