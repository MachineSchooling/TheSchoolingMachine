import urllib
import zipfile
import json
import os.path
from pprint import pprint


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


def update(filename="AllCards.json"):
    zipfilename = filename + ".zip"

    urllib.urlretrieve("http://mtgjson.com/json/" + zipfilename, zipfilename)

    with zipfile.ZipFile(zipfilename) as jzip:
        jzip.extractall()


if not os.path.exists("AllCards.json"):
    update()


carddata = json.load(open("AllCards.json", 'r'))
cardnames = [english_form(card.encode('utf-8')) for card in carddata]

if __name__ == '__main__':
    update()
    pprint(cardnames)

    print "Cathartic Reunion" in cardnames
