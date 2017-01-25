import os
import urllib
import zipfile
import json
from pprint import pprint

# Open .json file as python data.
carddata = json.load(open("AllCards.json", 'r'))

def english_form(string):
    replacelist = [
        ('\xc2\xae', ''),
        ('\xc3\x86', 'Ae'),
        ('\xc3\xa0', 'a'),
        ('\xc3\xa1', 'a'),
        ('\xc3\xa2', 'a'),
        ('\xc3\xa9', 'e'),
        ('\xc3\xad', 'i'),
        ('\xc3\xb6', 'o'),
        ('\xc3\xba', 'u'),
        ('\xc3\xbb', 'u'),
    ]
    for i in replacelist:
        string = string.replace(*i)
    return string


def json_update():
    urllib.urlretrieve("http://mtgjson.com/json/AllCards.json.zip", "AllCards.json.zip")

    with zipfile.ZipFile("AllCards.json.zip") as jzip:
        jzip.extractall()


# List of names of every Magic card.
# Replace retired non-English characters from old cards with their normal English counterparts.
cardnames = [english_form(card.encode('utf-8')) for card in carddata]

if __name__ == '__main__':
    json_update()
    pprint(cardnames)

    print "Cathartic Reunion" in cardnames
