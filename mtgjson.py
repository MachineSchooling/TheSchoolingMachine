# -*- coding: utf-8 -*-

import urllib
import zipfile
import json
from pprint import pprint


def filename():
    return "AllCards.json"


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


def update(filename=filename()):
    zipfilename = filename + ".zip"

    urllib.urlretrieve("http://mtgjson.com/json/" + zipfilename, zipfilename)

    with zipfile.ZipFile(zipfilename) as jzip:
        jzip.extractall()


class MyDict(dict):
    pass


def load():
    jdict = json.load(open(filename(), 'r'))
    jmydict = MyDict(jdict)
    jmydict.cardnames = [english_form(card.encode('utf-8')) for card in jdict]
    return jmydict


if __name__ == '__main__':
    update()
    carddata = load()
    cardnames = carddata.cardnames

    pprint(cardnames)

    print "As Foretold" in cardnames
