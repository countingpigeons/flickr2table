'''
TODO:
1.) add additional INSERT block which checks if Flickr_id was deleted but not
    re-inserted. If so, process these inserts again w/out parsing the
    description field. Set columns to "Failed to Parse" or "ERROR"
3.) re-factor to UPDATE records that have changed, instead of deleting and
    inserting these. not essential.
5.) add a bulk delete and backfill once per week to scheduler.
    5.1) if backfill, for each record in airtable, delete.
6.) user documentation. e.g. - to freeze records, change/delete Flickr_id col.
7.) add logging.

LOG:
2020-11-11: delete old single versions of newly joined multi-pic flower.
2020-08-10: first production version.
'''

from datetime import datetime
import time
import os.path as path
import argparse
import json
import re
from config import AirTableConfig
import airtable as at


apikey = AirTableConfig.apikey
base_id = AirTableConfig.flora_base_id
airtable = at.Airtable(base_id, apikey, dict)
table_name = 'FLORA'


def pretty_json(dict):
    pretty_string = json.dumps(dict, indent=2, sort_keys=True)
    return pretty_string


def parse_description(description: str = 'No description given.') -> dict:
    new_dict = {}
    lines = description.replace('&quot;', '"').splitlines()

    if lines:
        # if first line has =, don't steal as title,
        # unless it also has a period preceding the =, so just missing \n'
        if (not re.search(r'=', lines[0])) or (re.search(r'\..+=', lines[0])):
            new_dict['Genus + Species'] = lines.pop(0).rstrip('.')
        for line in lines:
            match = re.search(r'(.+)=(.+)', line)
            if match:
                key = match.groups()[0].strip()
                value = match.groups()[1].strip().rstrip('.')
                multiselect_columns = ['Color(s)']
                if key in multiselect_columns:
                    if value != '':
                        new_dict[key] = [item.strip().rstrip('.')
                                         for item in value.split(',')]
                else:
                    new_dict[key] = value
                # fix bad data
                if key == 'Secundo Location':
                    new_dict['Secondo Location'] = value
                    del new_dict[key]
    return new_dict


def camel_case_split(str):
    if re.search(' ', str):
        return str.rstrip('.')
    else:
        return ' '.join(re.findall(
            r'[A-Z](?:[a-z-\?\u2019]+|[A-Z]*(?=[A-Z]|$))', str)).rstrip('.')


def main():
    # run_date = '2020-08-06'
    run_date = datetime.today().date().strftime('%Y-%m-%d')
    parser = argparse.ArgumentParser()
    parser.add_argument("--album_name",
                        help="name as it appears in Flickr UI' "
                        "(default \'Flora\')",
                        default='Flora')
    parser.add_argument("--backfill", help="import all photos from album",
                        action="store_true")
    args = parser.parse_args()

    directory = '/home/koya/datascience/flickr_to_airtable/flickr_exports/'
    file_name = f'flickr_album_{args.album_name}_{run_date}'
    if args.backfill:
        file_name = file_name + '__full'
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
        flickr_raw_tags = photo['tags']
        flickr_tags = flickr_raw_tags.split(' ')
        prefix_primary_photo = '1' if 'primary' in flickr_tags else '2'
        download_filename = (prefix_primary_photo
                             + '_'
                             + path.basename(download_url))
        this_dict = {title: {
            'num_photos': 1,
            'lowest_flickr_id': flickr_id,
            'flickr_ids': [flickr_id],
            'flickr_id_to_use': flickr_id,
            'Image(s)': [{'url': download_url, 'filename': download_filename}],
            'Map Link': photo['google_map_url'],
            'Coordinates': photo['coordinates'],
            'Date Seen': photo['datetaken'],
            'Flickr_description': flickr_description,
            'Flickr Link': photo['flickr_url'],
            'Flickr_tags': flickr_raw_tags,
            'Common Name': camel_case_split(title)
        }}

        parsed_tags = parse_description(this_dict[title]['Flickr_description'])
        this_dict[title].update(parsed_tags)

        if title in master_dict:
            master_dict[title]['num_photos'] += 1
            master_dict[title]['Image(s)'].append(
                {'url': download_url, 'filename': download_filename})
            master_dict[title]['Image(s)'].sort(
                key=lambda x: (x['filename'], x['url']))
            if master_dict[title]['lowest_flickr_id'] > flickr_id:
                master_dict[title]['lowest_flickr_id'] = flickr_id
            master_dict[title]['flickr_ids'].append(flickr_id)
            master_dict[title]['flickr_ids'].sort()
            master_dict[title]['flickr_id_to_use'] = '_'.join(
                master_dict[title]['flickr_ids'])

        else:
            master_dict.update(this_dict)

    # print(pretty_json(master_dict))
    # return

    airtable_ids = {}
    airtable_records = airtable.iterate(table_name)

    for record in airtable_records:
        # Fixed. Ignore empty/bad rows in airtable.
        if 'fields' in record:
            if 'Flickr_id' in record['fields']:
                flickr_id = record['fields']['Flickr_id']
                airtable_id = record['id']
                airtable_ids[flickr_id] = airtable_id

    flickr_delete_ids = []
    # delete those to be re-inserted and any singles that may now be grouped
    for name, fields in master_dict.items():
        delete_id = fields['flickr_id_to_use']
        flickr_delete_ids.append(delete_id)
        if delete_id.find('_') > 0:
            delete_ids = delete_id.split('_')
            flickr_delete_ids.extend(delete_ids)
    # delete those lingering groups that are now split or re-grouped elsewhere
    for flickr_id, airtable_id in airtable_ids.items():
        if flickr_id.find('_') > 0:
            flickr_ids = flickr_id.split('_')
            flickr_ids = list(filter(lambda x: x in flickr_delete_ids,
                                     flickr_ids))
            if flickr_ids and flickr_id not in flickr_delete_ids:
                flickr_delete_ids.append(flickr_id)

    if args.backfill:
        airtable_delete_ids = list(airtable_ids.values())
    else:
        airtable_delete_ids = [
            val for key, val in airtable_ids.items()
            if key in flickr_delete_ids]

    for record_id in airtable_delete_ids:
        delete_response = airtable.delete(table_name, record_id)
        print(delete_response)
        time.sleep(.20)

    # final scrub - split out to allow debug
    for name, record in master_dict.items():
        record['Flickr_id'] = record['flickr_id_to_use']
        del record['flickr_id_to_use']
        del record['flickr_ids']
        del record['num_photos']
        del record['lowest_flickr_id']

        upload = airtable.create(table_name, data=record)
        # TO DO: add try/except. If id line fails, print {name} failed.
        print(f"uploaded: {upload['id']}, flickr name: {name}")
        time.sleep(.20)


if __name__ == '__main__':
    main()
