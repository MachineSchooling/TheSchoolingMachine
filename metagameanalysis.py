from pprint import pprint
import json

from mtgexceptions import CardError
from mtgexceptions import DeckError

"""
Mathematical justification for the probabilities we will report:

Bayes theorem: P[A|B]=P[B|A]P[A]/P[B]
A = archetype is being played
B = card is seen
P[A] = metagame share
P[B] = normalization factor
P[B|A] = percent of decks in archetype playing card * (number played in archetype/60)
P[A|B] is what we want to know the value of

P[A|B]P[B]=P[B|A]P[A]
SUM_A(P[A|B]P[B])=SUM_A(P[B|A]P[A])
P[B]SUM_A(P[A|B])=SUM_A(P[B|A]P[A])
P[B]=SUM_A(P[B|A]P[A]) since SUM_A(P[A|B])=1

P[A|B] = P[B|A]P[A]/SUM_A(P[B|A]P[A])


If B is the probability multiple cards are seen:

P[B] = P[B1]P[B2]...P[BN]

"""


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
    outtable = [(archetype, percent(probability)) for archetype, probability in intable[:maxrows] if probability>threshold]

    return outtable


def metagameDistribution(cardlist, magicFormat='modern', medium="online", maxrows=5, threshold=.05):
    """
    :param cardlist: Array of cards to be searched.
    :param magicFormat: String passed to MTGGoldfish url.
    :return: List of decks and their associated probabilities. List: (Deck, Probability P[A|B])
    """

    f = open("metagameDict.json", 'r')
    metagameDict = json.loads(f.read())
    f.close()

    outputTable = []

    # Populate the output table.
    for archetype in metagameDict:

        outputPercent = 0

        # outputPercent = P[B|A]
        try:
            for page in metagameDict[archetype]['pages']:

                deckDict = metagameDict[archetype]['pages'][page]['cards']

                outputPercent += metagameDict[archetype]['share']\
                                 * deckDict['maindeck'][cardlist]['frequency']\
                                 * deckDict['maindeck'][cardlist]['quantity']\
                                 / 60

        except (KeyError, AttributeError):
            pass

        outputTable.append((archetype, outputPercent))

    # Sort by likelihood.
    outputTable = sorted(outputTable, key=lambda deck: deck[1], reverse=True)

    # Implement the normalization factor P[B].
    normalizationFactor = sum([probability for archetype, probability in outputTable])
    # Only normalize if everything isn't already zero.
    if normalizationFactor:
        outputTable = [(archetype, probability / normalizationFactor) for archetype, probability in outputTable]

    return plausibile(outputTable, maxrows, threshold)


def metagameRunning(archetype, card):
    """
    :param archetype: Deck archetype name string.
    :param card: Cardame string.
    :return: [Expected number in maindeck rounded string, Expected number in sideboard rounded string]
    """

    f = open("metagameDict.json", 'r')
    metagameDict = json.loads(f.read())
    f.close()

    outdict = {}

    for board in ['maindeck', 'sideboard']:

        # Check if the queried deck is in the metagame archetypes list. If not, raise a deck error.
        try:
            metagameDict[archetype]
        except:
            raise DeckError(archetype)


        outnumber = 0

        try:
            for page in metagameDict[archetype]['pages']:
                deckDict = metagameDict[archetype]['pages'][page]['cards']

                outnumber += metagameDict[archetype]['pages'][page]['subshare'] \
                             * deckDict[board][card]['frequency'] \
                             * deckDict[board][card]['quantity']

        except KeyError:
            pass

        # Format the expected numbers for human readability.
        outdict[board] = humanform(outnumber)

    return outdict


f = open("metagameDict.json", 'r')
metagameDict = json.loads(f.read())
f.close()
options = [str(i) for i in metagameDict]


#pprint(metagameDistribution('Dark Confidant'))

#print metagameRunning("Jind", "Etched Champion")
