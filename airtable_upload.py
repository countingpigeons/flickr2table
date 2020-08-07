import json
from counting_pigeons_config import AirTableConfig
import airtable as at


def pretty_json(dict):
    json_string = json.dumps(dict, indent=2, sort_keys=True)
    return json_string


apikey = AirTableConfig.apikey
base_id = AirTableConfig.development_base_id
# base_id = AirTableConfig.flora_base_id

airtable = at.Airtable(base_id, apikey, dict)
table_name = 'yosemite'

# print(help(airtable))

# result = airtable.get(table_name)  # , 'rec8TbKVkYBcx6qE8')
# print(len(result['records']))
# # print(pretty_json(result))
#
# record_id = -1
# for record in result['records']:
#     flickr_id = record['fields']['Flickr_id']
#     if flickr_id == '456':
#         record_id = record['id']
# if record_id != -1:
#     # print(f'record_id: {record_id}, flickr_id: {flickr_id}, row_id: {record_id}')
#     print(f'record_id: {record_id}')

# bad_record = airtable.get(table_name, record_id)
# print(pretty_json(bad_record))
# bad_record = airtable.delete(table_name, record_id)
# print(bad_record)

# record to copy
# record_id = -1
# for record in result['records']:
#     flickr_id = record['fields']['Flickr_id']
#     if flickr_id == '123':
#         record_id = record['id']
#
# copy_record = airtable.get(table_name, record_id)
# copy_record['fields']['Name'] = 'NewRowInserted'
# del copy_record['id']

# print(copy_record['Name'])
# print(pretty_json(copy_record))
# print(copy_record.keys())
# print(copy_record['fields']['Name'])

# records = []
# records.append(copy_record)
# payload = {"records": [{"fields": [{"Name": "thisname"}]}]}
# print(help(json))
# {"records": [records]}

# payload = {"records": [
#     {
#         "fields": {
#             "Name": "Jd n Logan [2]"}}]}

data = {"Name": "AnotherName",
        # "Image(s)": [{"url": "https://live.staticflickr.com/65535/49671531862_583e980814_o.jpg"},
        #              {"url": "https://live.staticflickr.com/65535/49670721138_b23eccfeb9_o.jpg"}],
        # "Color": "Yellow",
        # "PlantType": ["Vine", "Flower"],
        "Color": "Green",
        "DateTaken": "2008-12-01"}

# print(type(payload))
print(pretty_json(data))

upload = airtable.create(table_name, data=data)
print(upload)


# for field in record['fields']:
#     print(field)
#         if field['Flickr_id'] == '456':
#             rowid = record['id']
#         else:
#             rowid = -1
#
# print(rowid)

# PREV WORKS
# auth_headers = {'Content-type': 'application/json',
#                 'Authorization': f'Bearer {apikey}'}
#
#
# def pretty_json(json_response) -> str:
#     pretty_string = json.dumps(json_response, indent=2, sort_keys=True)
#     return pretty_string
#
#
# # url = ('https://api.airtable.com/v0/appl1aRzPZnabDFpM'
# #        '/FLORA?maxRecords=3&view=Grid%20view')
# url = ('https://api.airtable.com/v0/appCXvmzt4Nmc8vyE'
#        '/yosemite?maxRecords=3&view=Grid%20view')
# development_base = 'appCXvmzt4Nmc8vyE'
#
# response = requests.get(url, headers=auth_headers)
#
# # print(type(response))
# # print(response.json()['records'])
#
# print(pretty_json(response.json()))
