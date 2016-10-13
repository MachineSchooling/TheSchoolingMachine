# JSON format is not necessary and the structure of the JSON has become unmanageably complex.
# metagame.py and metagameDict be replaced with a pickler and a python object with more intuitive structure.
# metagameanalysis with be similarly adjusted.

from pprint import pprint
from bs4 import BeautifulSoup
import urllib2
import re
import json


def stringTryToFloat(x):
    # Converts MTGGoldfish reported data into floats if they're numbers.
    try:
        return float(x)
    except ValueError:
        try:
            return float(x.strip('%')) / 100
        except ValueError:
            return x

def cleanName(name):
    # Takes a cardname with art specification and returns just the card's name. (Removes everything in parentheses.)
    regexDel = "\(([^\)]+)\)"
    return unicode(re.sub(regexDel, "", name).strip())


def cleanNumber(number):
    # Cleans up whitespace and NUMx from MTGGoldfish HTML and converts to float.
    return stringTryToFloat(number.strip().strip('x'))


def deckDict(deck):
    """
    Given a deck archetype's page, create a table which shows the amount of each card played in the deck.
    :param deck: url string
    :return: Dictionary: {'maindeck': {cardname: {'frequency':float, 'number':int}},
                            'sideboard': {cardname: {'frequency':float, 'number':int}}
                            }
    """

    url = deck
    page = urllib2.urlopen(url).read()
    fullsoup = BeautifulSoup(page, "lxml")

    soup = fullsoup.find('div', class_="archetype-details")  # needs 'class_' since 'class' is protected

    outputDict = {'maindeck':{}, 'sideboard':{}}

    # Handle split cards <-- NEED TO DO

    # Populate the dict.
    for cardTypeSubsection in soup.find_all('div', class_="archetype-breakdown-section"):

        # Populate the dict differentiating between the maindeck/sideboard cards.
        # Populate dict with maindeck cards.
        if cardTypeSubsection.find('h4').contents[0] != "Sideboard":
            # Populate the dict from the featured/unfeatured cards separately.
            for featured in cardTypeSubsection.find_all('div', class_="archetype-breakdown-featured-card"):
                try:
                    cardName = cleanName(featured.find('img')['alt'])
                    freqqty = featured.find('p', class_="archetype-breakdown-featured-card-text").contents[0]
                    cardFreqency = cleanNumber(re.search("[0-9]+%", freqqty).group(0))
                    cardQuantity = int(cleanNumber(re.search("[0-9]+x", freqqty).group(0)))
                    outputDict['maindeck'][cardName] = {'frequency': cardFreqency, 'quantity': cardQuantity}
                except AttributeError:
                    pass
            for unfeatured in cardTypeSubsection.find_all('tr'):
                try:
                    cardName = cleanName(unfeatured.find('a').contents[0])
                    cardFreqency = cleanNumber(unfeatured.find('td', class_="deck-col-frequency").contents[0])
                    cardQuantity = int(cleanNumber(unfeatured.find('td', class_="deck-col-qty").contents[0]))
                    outputDict['maindeck'][cardName] = {'frequency': cardFreqency, 'quantity': cardQuantity}
                except AttributeError:
                    pass

        # Populate dict with sideboard cards.
        else:
            # Populate the dict from the featured/unfeatured cards separately.
            for featured in cardTypeSubsection.find_all('div', class_="archetype-breakdown-featured-card"):
                try:
                    cardName = cleanName(featured.find('img')['alt'])
                    freqqty = featured.find('p', class_="archetype-breakdown-featured-card-text").contents[0]
                    cardFreqency = cleanNumber(re.search("[0-9]+%", freqqty).group(0))
                    cardQuantity = int(cleanNumber(re.search("[0-9]+x", freqqty).group(0)))
                    outputDict['sideboard'][cardName] = {'frequency': cardFreqency, 'quantity': cardQuantity}
                except AttributeError:
                    pass
            for unfeatured in cardTypeSubsection.find_all('tr'):
                try:
                    cardName = cleanName(unfeatured.find('a').contents[0])
                    cardFreqency = cleanNumber(unfeatured.find('td', class_="deck-col-frequency").contents[0])
                    cardQuantity = int(cleanNumber(unfeatured.find('td', class_="deck-col-qty").contents[0]))
                    outputDict['sideboard'][cardName] = {'frequency': cardFreqency, 'quantity': cardQuantity}
                except AttributeError:
                    pass

    return(outputDict)

def metagameDict(magicFormat="modern", medium="online"):
    """
    Create a dict which shows how much of the online Modern metagame is taken up by which decks and has a link to
    each of those decks' details page.
    :param magicFormat:
    :param medium:
    :return: Dict: {archetypeName: {'pages': {url: {'cards': SUBDICT, 'subshare': float}}, 'share': float}}
    from deckDict function SUBDICT: {cardname: {'frequency':float, 'number':int}}
    """
    # Get the data from MTGGoldfish.com.
    url = "https://www.mtggoldfish.com/metagame/" + magicFormat + "/full#" + medium
    page = urllib2.urlopen(url).read()
    fullsoup = BeautifulSoup(page, "lxml")
    soup = fullsoup.find("div", class_="metagame-list-full-content")  # needs 'class_' since 'class' is protected

    outputDict = {}

    # Create the table from the metagame summary page.
    for archetype in soup.find_all(class_="archetype-tile"):
        try:
            # Metagame share as it appears on main metagame page.
            archetypePercent = stringTryToFloat((archetype.find(class_="percentage col-freq").contents[0]).strip('\n'))
            # Decklist url for archetype. (url is non-unique for archetype names.)
            archetypeLink = archetype.find('a', class_="card-image-tile-link-overlay")["href"]
            # Name of archetype as it appears on main metagame page.
            archetypeName = archetype.find('a', href=archetypeLink + "#online").contents[0]
            # If no other decklist url exists for the given archetype name, create its listing in the dict.
            if archetypeName not in outputDict:
                outputDict[archetypeName] = {'share': 0, 'pages': {}}

            # Add the decklist url and its data to the named archetype's entry in the dict.
            decklist = "https://www.mtggoldfish.com" + archetypeLink
            # Create the listing for the decklist in the dict.
            outputDict[archetypeName]['pages'][decklist] = {}
            # Add the decklist's card info and subshare to the dict.
            outputDict[archetypeName]['pages'][decklist]['cards'] = deckDict(decklist)
            outputDict[archetypeName]['pages'][decklist]['subshare'] = archetypePercent
        except TypeError:
            pass

    # Normalize the shares of decklists with the same archetype name and assign the archetype a total share.
    #   Total share is located at outputDict[archetype]['share']
    #   Subshares are located at outputDict[archetype]['pages']['share']
    for archetype in outputDict:
        # Initialize the total share.
        outputDict[archetype]['share'] = 0
        for decklist in outputDict[archetype]['pages']:
            # Accumulate the total share.
            outputDict[archetype]['share'] += outputDict[archetype]['pages'][decklist]['subshare']
        # Normalize the subshares.
        for decklist in outputDict[archetype]['pages']:
            outputDict[archetype]['pages'][decklist]['subshare'] /= outputDict[archetype]['share']

    # See how much of the metagame is accounted for by named decks (the total accounted for shares).
    totalAccounted = sum([outputDict[archetype]['share'] for archetype in outputDict])
    # Scale the named decks' metagame shares by the total share accounted for.
    for archetype in outputDict:
        outputDict[archetype]['share'] = outputDict[archetype]['share'] / totalAccounted

    return(outputDict)


def jsonupdate(magicFormat="modern", medium="online"):
    f = open("metagameDict.json", 'w')
    f.write(json.dumps(metagameDict(magicFormat, medium)))
    f.close()


#jsonupdate()


#pprint(metagameDict(), width=2000)

#pprint(deckDict("https://www.mtggoldfish.com/archetype/modern-robots#online"))