from bs4 import BeautifulSoup
import urllib2
import re
import bisect
import cPickle
import math
import time
from scipy.stats import hypergeom


from pprint import pprint
import sys
sys.setrecursionlimit(10000)

from mtgexceptions import CardError
from mtgexceptions import DeckError



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
    return str(re.sub(regexDel, "", name).strip())

def cleanNumber(number):
    # Cleans up whitespace and NUMx from MTGGoldfish HTML and converts to float.
    return stringTryToFloat(number.strip().strip('x'))


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



class card(dict):
    #FINISHED
    def __init__(self, name, number=0, percent=1):
        self.name = name
        self[number] = percent
        if number != 0:
            self[0] = 1 - percent

    #FINISHED
    def __missing__(self, key):
        return 0

    #FINISHED
    def __lt__(self, other):
        return self.average() < other.average()

    #FINISHED
    def __str__(self):
        return "{} {}".format(self.average(), self.name)

    #FINISHED
    __repr__ = __str__

    #FINISHED
    def average(self):
        return reduce((lambda x, y: x + y), [number * self[number] for number in self])

    #FINISHED
    def __add__(self, other):
        if not self.name == other.name:
            raise CardError("Cards with different names can't be combined.")

        outcard = card(name=self.name)

        for number in set(self.keys()) | set(other.keys()):
            outcard[number] = self[number] + other[number]

        return outcard

    __radd__ = __add__

    # FINISHED
    def __mul__(self, scalar):
        outcard = card(name=self.name)

        for number in self.keys():
            outcard[number] = self[number] * scalar

        return outcard

    __rmul__ = __mul__


class board(dict):
    #FINISHED
    def size(self):
        #return sum(self.values())
        return sum(self[card].average() for card in self)

    #FINISHED
    def __missing__(self, key):
        return card(name=key)

    #FINISHED
    def __add__(self, other):
        outboard = board()

        for cardname in set(self) | set(other):
            outboard[cardname] = self[cardname] + other[cardname]

        return outboard

    __radd__ = __add__

    #FINISHED
    def __mul__(self, scalar):
        outboard = board()

        for cardname in self:
            outboard[cardname] = self[cardname] * scalar

        return outboard

    __rmul__ = __mul__


class decklist(object):
    def __init__(self, archetype, url=None, rawshare=0):
        self.url = url
        self.archetype = archetype
        self.main = board()
        self.side = board()
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
                    cardName = cleanName(featured.find('img')['alt'])
                    freqqty = featured.find('p', class_="archetype-breakdown-featured-card-text").contents[0]
                    cardFreqency = cleanNumber(re.search("[0-9]+%", freqqty).group(0))
                    cardQuantity = int(cleanNumber(re.search("[0-9]+x", freqqty).group(0)))

                    # Insert the decklist data into the metagame differentiating between the maindeck/sideboard cards.
                    if cardTypeSubsection.find('h4').contents[0] != "Sideboard":
                        self.main[cardName] = card(cardName, cardQuantity, cardFreqency)
                    else:
                        self.side[cardName] = card(cardName, cardQuantity, cardFreqency)
                except AttributeError:
                    pass

            for unfeatured in cardTypeSubsection.find_all('tr'):
                try:
                    # Collect the decklist data from MTGGoldfish.
                    cardName = cleanName(unfeatured.find('a').contents[0])
                    cardFreqency = cleanNumber(unfeatured.find('td', class_="deck-col-frequency").contents[0])
                    cardQuantity = int(cleanNumber(unfeatured.find('td', class_="deck-col-qty").contents[0]))

                    # Insert the decklist data into the metagame differentiating between the maindeck/sideboard cards.
                    if cardTypeSubsection.find('h4').contents[0] != "Sideboard":
                        self.main[cardName] = card(cardName, cardQuantity, cardFreqency)
                    else:
                        self.side[cardName] = card(cardName, cardQuantity, cardFreqency)
                except AttributeError:
                    pass


    #WORKING
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

    def __iter__(self):
        return iter(self.cards())

    def __str__(self):
        return str({'maindeck': self.main, 'sideboard': self.side})

    __repr__ = __str__

    #WORKING
    def __add__(self, other):
        if not self.archetype is other.archetype:
            raise DeckError("Decklists of different archetypes can't be combined.")

        outdecklist = decklist(archetype=self.archetype, rawshare=self.rawshare + other.rawshare)

        outdecklist.main = self.main + other.main
        outdecklist.side = self.side + other.side

        return outdecklist

    __radd__ = __add__

    # WORKING
    def __mul__(self, scalar):
        outdecklist = decklist(archetype=self.archetype, rawshare=self.rawshare*scalar)

        outdecklist.main = self.main * scalar
        outdecklist.side = self.side * scalar

        return outdecklist

    __rmul__ = __mul__


class archetype(decklist):
    def __init__(self, metagame, name):
        self.archetype = self
        self.name = name
        self.metagame = metagame
        self.sublists = []
        self.main = board()
        self.side = board()

    # FINISHED
    def insort(self, item):
        # Add the decklist to the archetype's list of decklists.
        bisect.insort(self.sublists, item)

        # Merge the decklist with the archetype decklist.
        totalshare = self.rawshare() + item.rawshare
        oldshare = self.rawshare() / totalshare
        newshare = item.rawshare / totalshare
        self.main = self.main * oldshare + item.main * newshare
        self.side = self.main * oldshare + item.side * newshare

    # FINISHED
    def rawshare(self):
        return sum(sublist.rawshare for sublist in self.sublists)

    def subshare(self):
        return 1

    #FINISHED
    def share(self):
        try:
            return self.rawshare() / self.metagame.accounted()
        except ZeroDivisionError:
            return 0

    # FINISHED
    def url(self):
        # Use only insort to insert into the archetype so the largest share decklist is always last.
        return self.sublists[-1].url

    #FINISHED
    def averagedecklist(self):
        # Decklist object formed from the weighted subshares of decklists within the archetype.
        return reduce((lambda x, y: x + y), [deck * deck.subshare() for deck in self.sublists])



class metagame(dict):
    def __init__(self, format):
        self.format = format
        self.populate()

    def accounted(self):
        # amount of metagame accounted for
        return sum(self[archetype].rawshare() for archetype in self)

    def populate(self):
        url = "https://www.mtggoldfish.com/metagame/" + self.format + "/full#online"
        page = urllib2.urlopen(url).read()
        fullsoup = BeautifulSoup(page, "lxml")
        soup = fullsoup.find("div", class_="metagame-list-full-content")

        for archetypeTile in soup.find_all(class_="archetype-tile"):
            try:
                # Collect the archetype data from MTGGoldfish.

                # Archetype tile metagame share as it appears on main metagame page.
                archetypePercent = stringTryToFloat(
                    (archetypeTile.find(class_="percentage col-freq").contents[0]).strip('\n'))
                # Archetype tile url. (url is non-unique for archetype names.)
                archetypeLink = archetypeTile.find('a', class_="card-image-tile-link-overlay")["href"]
                # Add the decklist url and its data to the named archetype's entry in the dict.
                archetypeURL = "https://www.mtggoldfish.com" + archetypeLink
                # Name of archetype as it appears on main metagame page.
                archetypeName = archetypeTile.find('a', href=archetypeLink + "#online").contents[0]

                # If no other archetype tiles have this one's name, create its listing.
                if archetypeName not in self:
                    currentArchetype = archetype(metagame=self, name=archetypeName)
                    self[archetypeName] = currentArchetype
                else:
                    currentArchetype = self[archetypeName]

                # Insert the archetype data into the metagame.

                # Create the listing for the decklist in the dict.
                currentArchetype.insort(
                    decklist(archetype=currentArchetype, url=archetypeURL, rawshare=archetypePercent)
                    )
            except TypeError:
                pass

    #WORKING
    def whatdeck(self, carddict):
        rawProbabilities = {archetype: self[archetype].thisdeck(carddict) * self[archetype].share()
                            for archetype in self}

        accounted = sum(rawProbabilities.values())

        probabilities = {}
        for archetype in rawProbabilities:
            probabilities[archetype] = rawProbabilities[archetype] / accounted

        print 'probabilities', probabilities

        outtable = [(probabilities[archetype], archetype) for archetype in probabilities]
        outtable.sort(reverse=True)

        outtable = plausibile(outtable)

        return outtable


class metagamemaster(dict):
    def __init__(self):
        self.formats = ["Standard", "Modern", "Legacy", "Vintage", "Pauper"]
        for format in self.formats:
            self[format] = metagame(format)

    '''
    def populate(self):
        for format in self:
            format.unpopulate()? clear?
            format.populate()
    '''

    def pickle(self):
        f = open("metagamemaster.p", 'wb')
        cPickle.dump(self, f)
        f.close()

    def whatdeck(self, format="Modern"):
        return self[format].whatdeck()


def loadMetagameMaster():
    f = open("metagamemaster.p", 'rb')
    out = cPickle.load(f)
    f.close()
    return out


if __name__ == '__main__':

    start = time.time()
    master = metagamemaster()
    master.pickle()
    end = time.time()
    print 'Timing:', end - start

    master = loadMetagameMaster()

    print 'running:', master["Modern"]["Jund"]["Abrupt Decay"]

    print 'whatdeck:', master["Modern"].whatdeck({"Polluted Delta": 1})

    print 'whatdeck:', master["Modern"].whatdeck({"Polluted Delta": 4})

    print 'whatdeck:', master["Modern"].whatdeck({"Thalia, Guardian of Thraben": 2, "Thought-Knot Seer": 1})