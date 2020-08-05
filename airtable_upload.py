import requests
import json
from counting_pigeons_config import AirTableConfig

apikey = AirTableConfig.apikey
flora_base_id = AirTableConfig.flora_base_id

auth_headers = {'Content-type': 'application/json',
                'Authorization': f'Bearer {apikey}'}


def pretty_json(json_response) -> str:
    pretty_string = json.dumps(json_response, indent=2, sort_keys=True)
    return pretty_string


# url = ('https://api.airtable.com/v0/appl1aRzPZnabDFpM'
#        '/FLORA?maxRecords=3&view=Grid%20view')
url = ('https://api.airtable.com/v0/appCXvmzt4Nmc8vyE'
       '/yosemite?maxRecords=3&view=Grid%20view')
development_base = 'appCXvmzt4Nmc8vyE'

response = requests.get(url, headers=auth_headers)

# print(type(response))
# print(response.json()['records'])

print(pretty_json(response.json()))
