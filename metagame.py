# Import standard modules.
from bs4 import BeautifulSoup
import urllib2
import re
import bisect
import cPickle
import os
import sys
import time
from collections import namedtuple
from scipy.stats import hypergeom
# Import custom modules.
from mtgexceptions import CardError
from mtgexceptions import DeckError



sys.setrecursionlimit(10000)


def masterfile():
    return "metagamemaster.p"


def string_try_to_float(x):
    # Converts MTGGoldfish reported data into floats if they're numbers.
    try:
        return float(x)
    except ValueError:
        try:
            return float(x.strip('%')) / 100
        except ValueError:
            return x

def clean_name(name):
    # Takes a cardname with art specification and returns just the card's name. (Removes everything in parentheses.)
    regexDel = "\(([^\)]+)\)"
    return str(re.sub(regexDel, "", name).strip())

def clean_number(number):
    # Cleans up whitespace and NUMx from MTGGoldfish HTML and converts to float.
    return string_try_to_float(number.strip().strip('x'))


def percent(float, decimals=0):
    """
    :param float: Float to be rewritten as a percentage.
    :param decimals: Number of decimals to display.
    :return: 'N%' string.
    """
    return "{0:.{1}f}%".format(float * 100, decimals)

def humanform(number, decimals=1):
    """
    :param float: Float to be rewritten with specified significant digits.
    :param decimals: Number of decimals to display.
    :return: 'N.M' string.
    """
    if number == int(number):
        return str(number)
    else:
        return "{0:.{1}f}".format(number, decimals)

def plausibile(intable, maxrows=5, threshold=.05):
    """
    :param intable: Table of archetypes and associated probabilities.
    :param maxrows: Maximum number of archetypes to display.
    :param threshold: Minimum likelihood to display.
    :return: outtable is intable rows which satisfy max and threshold restrictions
    """
    outtable = [(percent(probability), archetype) for probability, archetype in intable[:maxrows] if probability>threshold]

    return outtable


class Card(dict):
    def __init__(self, name, number=0, percent=1):
        self.name = name
        self[number] = percent
        if number != 0:
            self[0] = 1 - percent

    def __missing__(self, key):
        return 0

    def __lt__(self, other):
        return self.average() < other.average()

    def __str__(self):
        return "{} {}".format(humanform(self.average()), self.name)

    __repr__ = __str__

    def average(self):
        return reduce((lambda x, y: x + y), [number * self[number] for number in self])

    def __add__(self, other):
        if not self.name == other.name:
            raise CardError("Cards with different names can't be combined.")

        outcard = Card(name=self.name)

        for number in set(self.keys()) | set(other.keys()):
            outcard[number] = self[number] + other[number]

        return outcard

    __radd__ = __add__

    def __mul__(self, scalar):
        outcard = Card(name=self.name)

        for number in self.keys():
            outcard[number] = self[number] * scalar

        return outcard

    __rmul__ = __mul__


class Board(dict):
    def size(self):
        return sum(self[card].average() for card in self)

    def __missing__(self, key):
        return Card(name=key)

    def __add__(self, other):
        outboard = Board()

        for cardname in set(self) | set(other):
            outboard[cardname] = self[cardname] + other[cardname]

        return outboard

    __radd__ = __add__

    def __mul__(self, scalar):
        outboard = Board()

        for cardname in self:
            outboard[cardname] = self[cardname] * scalar

        return outboard

    __rmul__ = __mul__


class Decklist(object):
    def __init__(self, archetype, url=None, rawshare=0):
        self.url = url
        self.archetype = archetype
        self.main = Board()
        self.side = Board()
        self.rawshare = rawshare # raw share of decklist in metagame
        self.populate()

    def cards(self):
        return self.main + self.side

    def size(self):
        return self.main.size() + self.side.size()

    def subshare(self):
        # share of the decklist among decks in the decklist's archetype
        try:
            return self.rawshare / self.archetype.share()
        except ZeroDivisionError:
            return 0

    def share(self):
        try:
            return self.rawshare / self.archetype.metagame.accounted()
        except ZeroDivisionError:
            return 0

    def populate(self):
        if self.url is not None:
            page = urllib2.urlopen(self.url).read()
            fullsoup = BeautifulSoup(page, "lxml")
            soup = fullsoup.find('div', class_="archetype-details")
        else:
            return None

        for cardTypeSubsection in soup.find_all('div', class_="archetype-breakdown-section"):
            # Collect the decklist data from MTGGoldfish from featured/unfeatured cards separately.
            for featured in cardTypeSubsection.find_all('div', class_="archetype-breakdown-featured-card"):
                try:
                    # Collect the decklist data from MTGGoldfish.
                    cardName = clean_name(featured.find('img')['alt'])
                    freqqty = featured.find('p', class_="archetype-breakdown-featured-card-text").contents[0]
                    cardFreqency = clean_number(re.search("[0-9]+%", freqqty).group(0))
                    cardQuantity = int(clean_number(re.search("[0-9]+x", freqqty).group(0)))

                    # Insert the decklist data into the metagame differentiating between the maindeck/sideboard cards.
                    if cardTypeSubsection.find('h4').contents[0] != "Sideboard":
                        self.main[cardName] = Card(cardName, cardQuantity, cardFreqency)
                    else:
                        self.side[cardName] = Card(cardName, cardQuantity, cardFreqency)
                except AttributeError:
                    pass

            for unfeatured in cardTypeSubsection.find_all('tr'):
                try:
                    # Collect the decklist data from MTGGoldfish.
                    cardName = clean_name(unfeatured.find('a').contents[0])
                    cardFreqency = clean_number(unfeatured.find('td', class_="deck-col-frequency").contents[0])
                    cardQuantity = int(clean_number(unfeatured.find('td', class_="deck-col-qty").contents[0]))

                    # Insert the decklist data into the metagame differentiating between the maindeck/sideboard cards.
                    if cardTypeSubsection.find('h4').contents[0] != "Sideboard":
                        self.main[cardName] = Card(cardName, cardQuantity, cardFreqency)
                    else:
                        self.side[cardName] = Card(cardName, cardQuantity, cardFreqency)
                except AttributeError:
                    pass


    def thisdeck(self, carddict):
        querysize = sum(carddict.values())
        decksize = int(self.main.size())
        probabilityUnion = self.subshare()

        for cardname in carddict:
            amounts = [number for number in self.main[cardname] if number != 0]

            # If the deck plays no copies the probability is zero.
            if not amounts: return 0

            for number in amounts:
                freq = self.main[cardname][number]
                actualsuccesses = carddict[cardname]
                successdraws = number
                cardsdrawn = querysize
                probabilityUnion *= hypergeom.pmf(k=actualsuccesses, M=decksize, n=successdraws, N=cardsdrawn) * freq

        return probabilityUnion


    def __getitem__(self, item):
        return {'maindeck': self.main[item], 'sideboard': self.side[item]}

    def __str__(self):
        return str({'maindeck': self.main, 'sideboard': self.side})

    __repr__ = __str__

    def __add__(self, other):
        if not self.archetype is other.archetype:
            raise DeckError("Decklists of different archetypes can't be combined.")

        outdecklist = Decklist(archetype=self.archetype, rawshare=self.rawshare + other.rawshare)

        outdecklist.main = self.main + other.main
        outdecklist.side = self.side + other.side

        return outdecklist

    __radd__ = __add__

    def __mul__(self, scalar):
        outdecklist = Decklist(archetype=self.archetype, rawshare=self.rawshare*scalar)

        outdecklist.main = self.main * scalar
        outdecklist.side = self.side * scalar

        return outdecklist

    __rmul__ = __mul__


class Archetype(Decklist):
    def __init__(self, metagame, name):
        self.archetype = self
        self.name = name
        self.metagame = metagame
        self.sublists = []
        self.main = Board()
        self.side = Board()

    # FINISHED
    def insort(self, item):
        # Merge the decklist with the archetype decklist.
        totalshare = self.rawshare() + item.rawshare
        oldshare = self.rawshare() / totalshare
        newshare = item.rawshare / totalshare
        self.main = self.main * oldshare + item.main * newshare
        self.side = self.side * oldshare + item.side * newshare

        # Add the decklist to the archetype's list of decklists.
        bisect.insort(self.sublists, item)

    def rawshare(self):
        return sum(sublist.rawshare for sublist in self.sublists)

    def subshare(self):
        return 1

    def share(self):
        try:
            return self.rawshare() / self.metagame.accounted()
        except ZeroDivisionError:
            return 0

    def url(self):
        # Use only insort to insert into the archetype so the largest share decklist is always last.
        return self.sublists[-1].url

    def averagedecklist(self):
        # Decklist object formed from the weighted subshares of decklists within the archetype.
        return reduce((lambda x, y: x + y), [deck * deck.subshare() for deck in self.sublists])


class Metagame(dict):
    def __init__(self, format_):
        self.format_ = format_
        self.populate()

    def accounted(self):
        # amount of metagame accounted for
        return sum(self[archetype].rawshare() for archetype in self)

    def populate(self):
        url = "https://www.mtggoldfish.com/metagame/" + self.format_ + "/full#online"
        page = urllib2.urlopen(url).read()
        fullsoup = BeautifulSoup(page, "lxml")
        soup = fullsoup.find("div", class_="metagame-list-full-content")

        for archetypeTile in soup.find_all(class_="archetype-tile"):
            try:
                # Collect the archetype data from MTGGoldfish.

                # Archetype tile metagame share as it appears on main metagame page.
                archetypePercent = string_try_to_float(
                    (archetypeTile.find(class_="percentage col-freq").contents[0]).strip('\n'))
                # Archetype tile url. (url is non-unique for archetype names.)
                archetypeLink = archetypeTile.find('a', class_="card-image-tile-link-overlay")["href"]
                # Add the decklist url and its data to the named archetype's entry in the dict.
                archetypeURL = "https://www.mtggoldfish.com" + archetypeLink
                # Name of archetype as it appears on main metagame page.
                archetypeName = archetypeTile.find('a', href=archetypeLink + "#online").contents[0]

                # If no other archetype tiles have this one's name, create its listing.
                if archetypeName not in self:
                    currentArchetype = Archetype(metagame=self, name=archetypeName)
                    self[archetypeName] = currentArchetype
                else:
                    currentArchetype = self[archetypeName]

                # Insert the archetype data into the metagame.

                # Create the listing for the decklist in the dict.
                currentArchetype.insort(
                    Decklist(archetype=currentArchetype, url=archetypeURL, rawshare=archetypePercent)
                    )
            except TypeError:
                pass


    def whatdeck(self, carddict):
        rawProbabilities = {archetype: self[archetype].thisdeck(carddict) * self[archetype].share()
                            for archetype in self}

        accounted = sum(rawProbabilities.values())
        if not accounted: return []

        probabilities = {archetype: rawProbabilities[archetype] / accounted for archetype in rawProbabilities}

        outtable = [(probabilities[archetype], archetype) for archetype in probabilities]
        outtable.sort(reverse=True)

        outtable = plausibile(outtable)

        return outtable

    def archetypes(self):
        formatarchetype = namedtuple("formatarchetype", ["format_", "archetype"])
        return [formatarchetype(self.format_, archetype) for archetype in self]


class MetagameMaster(dict):
    def __init__(self):
        self.formats = ["Standard", "Modern", "Legacy", "Vintage", "Pauper"]
        for format_ in self.formats:
            self[format_] = Metagame(format_)
        self.pickle()

    def pickle(self):
        f = open(masterfile(), 'wb')
        cPickle.dump(self, f)
        f.close()

    def lastUpdate(self):
        os.path.getmtime(masterfile())

    def whatdeck(self, format_, carddict):
        return self[format_].whatdeck(carddict)

    def running(self, format_, archetype, cardname):
        return self[format_][archetype][cardname]

    def archetypes(self):
        formatarchetype = namedtuple("formatarchetype", ["format_", "archetype"])
        return [formatarchetype(format_, archetype) for format_ in self for archetype in self[format_]]


def load():
    with open(masterfile(), 'rb') as f:
        out = cPickle.load(f)
        return out


if __name__ == '__main__':
    recalculate = False
    if recalculate:
        start = time.time()
        master = MetagameMaster()
        master.pickle()
        end = time.time()
        print 'Timing:', end - start

    master = load()

    print 'running:', master["Modern"]["Jund"]["Lightning Bolt"]
    print 'running:', master["Modern"]["Affinity"]["Cranial Plating"]
    print 'running:', master["Legacy"]["Miracles"]["Force of Will"]
    print 'whatdeck:', master["Modern"].whatdeck({"Tarmogoyf": 1})
    print 'whatdeck:', master.whatdeck("Modern", {"Tarmogoyf": 1})
    print 'whatdeck:', master["Modern"].whatdeck({"Polluted Delta": 1})
    print 'whatdeck:', master["Modern"].whatdeck({"Polluted Delta": 4})
    print 'whatdeck:', master["Modern"].whatdeck({"Thalia, Guardian of Thraben": 2, "Thought-Knot Seer": 1})
    print 'whatdeck:', master["Legacy"].whatdeck({"Mountain": 1, "Lightning Bolt": 1, "Monastery Swiftspear": 2})

    print "Legacy decks:", [a.archetype for a in master["Legacy"].archetypes()]

    print 'whatdeck:', master.whatdeck("Modern", {"Lightning Bolt": 1, "Polluted Delta": 2})