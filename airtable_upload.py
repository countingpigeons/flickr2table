from datetime import datetime
import time
import argparse
import json
import re
# import os.path as path
from counting_pigeons_config import AirTableConfig
import airtable as at


apikey = AirTableConfig.apikey
base_id = AirTableConfig.flora_base_id
airtable = at.Airtable(base_id, apikey, dict)
table_name = 'FLORA'


return_status = 0


def pretty_json(dict):
    pretty_string = json.dumps(dict, indent=2, sort_keys=True)
    return pretty_string


def parse_description(description: str = '') -> dict:
    if not description:
        description = 'Ribes sanguineum var. glutinosum.\nCommon Names = Pink-flowered Currant, Blood Currant, Southern pink flowering currant.\nFamily = Grossulariaceae.\nFamily Name = Currant and Gooseberry.\nType = Flowering Plant.\nColor(s) = Pink.\nPetal(s) = 5.\nPrimo Location = Golden Gate Park.\nSecundo Location = AIDS Memorial Grove creek bed.'
    new_dict = {}
    lines = description.splitlines()

    scientific_name = lines.pop(0).rstrip('.')
    new_dict['Genus + Species'] = scientific_name
    for line in lines:
        match = re.search(r'(.+)=(.+)', line)
        if match:
            key = match.groups()[0].strip()
            value = match.groups()[1].strip().rstrip('.')
            new_dict[key] = value
    return new_dict


def camel_case_split(str):
    if re.search(' ', str):
        return str.rstrip('.')
    else:
        return ' '.join(re.findall(
            r'[A-Z](?:[a-z-]+|[A-Z]*(?=[A-Z]|$))', str)).rstrip('.')


run_date = '2020-08-09'  # datetime.today().date().strftime('%Y-%m-%d')
parser = argparse.ArgumentParser()
parser.add_argument("--album_name",
                    help="name as it appears in Flickr UI' "
                    "(default \'Flora\')",
                    default='Flora')
parser.add_argument("--backfill", help="import all photos from album",
                    action="store_true")
args = parser.parse_args()


directory = 'flickr_exports/'
file_name = f'flickr_album_{args.album_name}_{run_date}'
if args.backfill:
    file_name = file_name + '_full'
file_name = file_name + '.json'

try:
    with open(directory+file_name, 'r') as f:
        contents = json.loads(f.read())
    return_status = 1
except FileNotFoundError as e:
    print(f'file not found. error: {e}')
    raise(e)
    return_status = 0

master_dict = {}
for photo in contents['photos']:
    title = photo['title']
    flickr_id = photo['id']
    download_url = photo['url_o']
    flickr_description = photo['description']
    this_dict = {title: {
        'num_photos': 1,
        'lowest_flickr_id': flickr_id,
        'flickr_ids': [flickr_id],
        'flickr_id_to_use': flickr_id,
        'Image(s)': [{'url': download_url}],
        'Map Link': photo['google_map_url'],
        'Coordinates': photo['coordinates'],
        'Date Seen': photo['datetaken'],
        'Flickr_description': flickr_description,
        'Flickr Link': photo['flickr_url'],
        'Common Name': camel_case_split(title),  # process: split on CAP, join w/ ' '

    }}
    parsed_tags = parse_description(this_dict[title]['Flickr_description'])
    this_dict[title].update(parsed_tags)
    if title in master_dict:
        master_dict[title]['num_photos'] += 1
        master_dict[title]['Image(s)'].append({'url': download_url})
        master_dict[title]['Image(s)'].sort(key=lambda x: x['url'])  # url should sort by flickrid
        if master_dict[title]['lowest_flickr_id'] > flickr_id:
            master_dict[title]['lowest_flickr_id'] = flickr_id
        master_dict[title]['flickr_ids'].append(flickr_id)
        master_dict[title]['flickr_ids'].sort()
        master_dict[title]['flickr_id_to_use'] = '_'.join(
            master_dict[title]['flickr_ids'])

    else:
        master_dict.update(this_dict)

# print(pretty_json(master_dict))


# for name, record in master_dict.items():
    # delete these records on airtable

    # final scrub - split out to allow debug
for name, record in master_dict.items():
    record['Flickr_id'] = record['flickr_id_to_use']
    del record['flickr_id_to_use']
    del record['flickr_ids']
    del record['num_photos']
    del record['lowest_flickr_id']

    upload = airtable.create(table_name, data=record)
    time.sleep(.25)
# print(pretty_json(master_dict))
