from counting_pigeons_config import FlickrConfig
from requests_oauthlib import OAuth1Session
import json
from datetime import datetime, timedelta
import sys
import argparse
import re

base_api_url = 'https://www.flickr.com/services/rest/?method=flickr.'
json_url_suffix = '&format=json&nojsoncallback=1'
# jsoncallback=1 else json is returned wrapped in a function
oauth = OAuth1Session(
    client_secret=FlickrConfig.secret,
    client_key=FlickrConfig.apikey,
    resource_owner_key=FlickrConfig.resource_owner_key_karen,
    resource_owner_secret=FlickrConfig.resource_owner_secret_karen)


def api_call(method: str, params: dict = {}) -> json:
    response = None
    protected_url = base_api_url + method + json_url_suffix
    # print(f'orig_url: {protected_url}')
    if params:
        param_string = ''
        for param, value in params.items():
            param_string += '&'+param+'='+value
        protected_url = protected_url + param_string
        # print(f'url with params: {protected_url}')
    response = oauth.get(protected_url).json()
    return response


def pretty_json(json_response) -> str:
    pretty_string = json.dumps(json_response, indent=2, sort_keys=True)
    return pretty_string


def get_user_id():
    method = 'test.login'
    response = api_call(method)
    user_id = response.get('user', {}).get('id', 0)
    return user_id


def get_albums_json(user_id):
    method = 'photosets.getList'
    params = {"user_id": user_id}
    response = api_call(method, params)
    return response


def get_album_details(user_id, album_name: str):
    response = get_albums_json(user_id)
    album_id = -1
    for photoset in response.get('photosets', {}).get('photoset'):
        title = photoset['title']['_content']
        if title == album_name:
            album_id = photoset['id']
            created = datetime.fromtimestamp(
                int(photoset['date_create'])).date().strftime('%Y-%m-%d')
            updated = datetime.fromtimestamp(
                int(photoset['date_update'])).date().strftime('%Y-%m-%d')
            num_photos = photoset['photos']
            return album_id, title, num_photos, created, updated
    return None


def get_album_photos_json(user_id, photoset_id, per_page=200, page=1):
    method = 'photosets.getPhotos'
    extras_string = 'geo,url_o,date_taken,date_upload,last_update,tags'
    params = {"user_id": user_id, "photoset_id": photoset_id,
              "extras": extras_string, "per_page": str(per_page),
              "page": str(page)}

    response = api_call(method, params)
    if response['stat'] == 'ok':
        response = response['photoset']
    else:
        raise ValueError("response['stat'] is not 'ok'")
    return response


def get_photo_info_json(photo_id, feature=None):
    method = 'photos.getInfo'
    params = {"photo_id": photo_id}
    response = api_call(method, params)['photo']

    title = response['title']['_content']
    ui_url = response['urls']['url'][0]['_content']
    last_update = datetime.fromtimestamp(int(response['dates']['lastupdate']))
    taken = response['dates']['taken']
    description = response['description']['_content']

    if feature == 'title':
        return title
    elif feature == 'ui_url':
        return ui_url
    elif feature == 'last_update':
        return last_update
    elif feature == 'taken':
        return taken
    elif feature == 'description':
        return description
    else:
        return response


def create_album_output(run_date, album_name: str, backfill=False) -> str:
    cutoff_7_days = datetime.today()-timedelta(days=7)
    user_id = get_user_id()
    album_id, album_title, album_num_photos, album_created, album_updated =\
        get_album_details(user_id, album_name)
    photos_per_page = 200
    pages = (album_num_photos // photos_per_page)
    if photos_per_page * pages < album_num_photos:
        pages += 1
    album_photos = []
    for page in range(1, pages+1):
        page_photos = get_album_photos_json(
            user_id,
            photoset_id=album_id,
            per_page=photos_per_page,
            page=page)['photo']
        album_photos.extend(page_photos)
    keys = ['datetaken', 'dateupload', 'id', 'lastupdate',
            'latitude', 'longitude', 'tags', 'title', 'url_o', 'flickr_url']
    filtered_album_photos = []
    album = {}
    album_latest_photo_update = '0'
    for photo in album_photos:
        if photo['lastupdate'] > album_latest_photo_update:
            album_latest_photo_update = photo['lastupdate']
        photo_id = photo['id']
        photo['dateupload'] = datetime.fromtimestamp(
            int(photo['dateupload'])).date().strftime('%Y-%m-%d')
        photo['lastupdate'] = datetime.fromtimestamp(
            int(photo['lastupdate'])).date().strftime('%Y-%m-%d')
        flickr_in_album_base_url = ('https://www.flickr.com/photos/{}/'
                                    '{}/in/album-{}/')
        photo['flickr_url'] = \
            flickr_in_album_base_url.format(user_id, photo_id, album_id)
        clean_photo = {mykey: photo[mykey] for mykey in keys}
        if backfill:
            cutoff = datetime.strptime('2010-01-01', '%Y-%m-%d')
        else:
            cutoff = cutoff_7_days

        fresh = datetime.strptime(
            clean_photo['lastupdate'], '%Y-%m-%d') > cutoff
        tbd = re.search('tbd', clean_photo['title'])
        if fresh and not tbd:
            clean_photo['description'] = get_photo_info_json(
                photo_id, 'description')
            filtered_album_photos.append(clean_photo)

    album['photos'] = filtered_album_photos
    album['id'] = album_id
    album['title'] = album_title
    if backfill:
        album['num_photos'] = album_num_photos
    else:
        album['num_photos'] = len(album['photos'])
    album['created'] = album_created
    album['updated'] = album_updated
    album['run_date'] = run_date
    album_latest_photo_update = datetime.fromtimestamp(
        int(album_latest_photo_update)).date().strftime('%Y-%m-%d')
    album['latest_photo_update'] = album_latest_photo_update
    return pretty_json(album)


def write_album_output(run_date, album_name, album):
    base_file_name = 'flickr_album_{}_{}.json'
    file_path = '/home/koya/datascience/flickr_to_airtable/flickr_exports/'
    file_name = base_file_name.format(album_name, run_date)
    full_path = file_path + file_name
    with open(full_path, 'w') as f:
        f.write(album)
        print(f'wrote album to: {full_path}')
    return 1


def main():

    run_date = datetime.today().date().strftime('%Y-%m-%d')
    parser = argparse.ArgumentParser()
    parser.add_argument("--album_name",
                        help="name as it appears in Flickr UI' "
                        "(default \'Flora\')",
                        default='Flora')
    parser.add_argument("--backfill", help="import all photos from album",
                        action="store_true")
    args = parser.parse_args()
    # print(f'album_name: {args.album_name}, backfill: {args.backfill}')

    album = create_album_output(run_date, args.album_name, args.backfill)
    export_success = write_album_output(run_date, args.album_name, album)

    return export_success


if __name__ == '__main__':
    main()


# print(pretty_json(get_albums_json(user_id)))

# photo_title = photo['title']
# photo_id = photo['id']
# photo_tags = photo['tags']
# photo_tags_list = photo_tags.replace('0', ':').split(' ')
# photo_taken = photo['datetaken']

# print(photo_title, photo_id, photo_description, photo_tags, photo_taken, photo_tags_list)
# print(pretty_json(album_photos))

# print(pretty_json(album_photos_json))


# if photo_title == 'IMG-20160607-00292':
#     photo_url = photo['url_o']
#     r = oauth.get(photo_url)
#     if r.status_code == 999:
#         with open(photo_title, 'wb') as f:
#             for chunk in r.iter_content(1024):
#                 f.write(chunk)
#         print('wrote file')

# jdnlogan photo "id" = 30239296361
# template for "flickr_link": "https://www.flickr.com/photos/karenoffereins/49692485441/in/album-72157714042432652/"


# for photoset in response.get('photosets')['photoset']:
#     title = photoset['title']['_content']
#     id = photoset['id']
#     num_photos = photoset['photos']
#     date_create = photoset['date_create']
#     # print(photoset['title']['_content'])
#     print(f'{id} ({title}) [{num_photos} photos]')
#     print(date_create)
#     print(datetime.fromtimestamp(int(date_create)))
# print(help(datetime))

# https://www.flickr.com/photos/41064584@N03/30209004042/
# https://www.flickr.com/photos/41064584@N03/30209004042/in/album-72157671703751344/
