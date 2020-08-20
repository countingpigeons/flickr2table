# Flickr2Table:

#### Uses the Flickr API to pull photos from a particular album, comingling any with same Title into a single record, and inserting records/rows with columns parsed from the Flickr description, tags, and geotagging into Airtable using the Airtable API. 

To use, you must create a config.py file (should amend to config.yaml) with API keys and other info. The FlickrAuthenticate module uses Oauth1 to get access tokens for a particular Flickr account to which you already have the username/password. 
