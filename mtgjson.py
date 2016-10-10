import os
import urllib
import zipfile
import json
from pprint import pprint

# If .json.zip file is not already downloaded, get .json.zip file.
if not os.path.exists("AllCards.json.zip"):
    urllib.urlretrieve("http://mtgjson.com/json/AllCards.json.zip", "AllCards.json.zip")

# If .json file is not already extracted, extract .json file from .zip.
if not os.path.exists("AllCards.json"):
    with zipfile.ZipFile("AllCards.json.zip") as jzip:
        jzip.extractall()


# Open .json file as python data.
carddata = json.load(open("AllCards.json", 'r'))

# List of names of every Magic card.
# Replace retired non-English characters from old cards with their normal English counterparts.
cardnames = [card.encode('utf-8').replace('\xc3\x86', 'Ae').replace('\xc3\xbb', 'u').replace('\xc3\xba', 'u')
             .replace('\xc3\xa1', 'a').replace('\xc3\xa9', 'e').replace('\xc3\xa0', 'a').replace('\xc3\xa2', 'a')
             .replace('\xc2\xae', '').replace('\xc3\xb6', 'o').replace('\xc3\xad', 'i')
             for card in carddata]

#pprint(cardnames)
