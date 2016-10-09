# Import standard modules.
import re
# Import custom modules.
from mtgexceptions import CardError
from mtgexceptions import DeckError
import metagame
from metagameanalysis import metagameDistribution
from metagameanalysis import metagameRunning
import mtgjson
#import fuzzycard


#FINISHED
def test(PRIVMSG):
    PRIVMSG.bot.chat(PRIVMSG.CHAN, "Hello, Twitch!")



def commands(PRIVMSG):
    """
    Links to a list of commands.
    :return: True if a !commands query call is sent to the IRC server. Else false.
    """
    PRIVMSG.bot.chat(PRIVMSG.CHAN, "You can find a list of my commands here: ")

#WORKING
def join(PRIVMSG):
    """
    Add command caller to list of users.
    :param args:
    :return:
    """
    if PRIVMSG.args.NICK:
        pass
    # Update users list and JOIN.


#WORKING
def decklist(PRIVMSG):
    """
    Fetch a decklist page from MTGGoldfish based on the deck name given.
    :param PRIVMSG:
    :return:
    """


#WORKING
def running(PRIVMSG):
    """
    Probability deck archetype is running cardname in maindeck and sideboard.
    :param PRIVMSG: pattern: !running deckname: cardname
    :return: message: N%
    """
    # Make sure the command's arguments are of the form "Deck Name: Card Name".
    try:
        args = PRIVMSG.args.split(':')
        archetype, card = [i.lstrip() for i in args]

        # Calculate and message the deck's average number of the card run.
        try:
            probabilities = metagameRunning(archetype, card)
            rawmessage = "The average {} deck runs {} copies of {} in the maindeck and {} in the sideboard."
            message = rawmessage.format(archetype, probabilities['maindeck'], card, probabilities['sideboard'])
            PRIVMSG.bot.chat(PRIVMSG.CHAN, message)
        # If the queried deck can't be found, message the user an error.
        except DeckError:
            message = str(DeckError(archetype))
            PRIVMSG.bot.chat(PRIVMSG.CHAN, message)

    # If the command arguments are improperly formatted, message the user an error.
    except ValueError:
        message = "Command format error. Command should be of the form '!running Archetype Name: Card Name'."
        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)



#WORKING
def whatdeck(PRIVMSG):
    """
    Calls Baysian Metagame Analysis program.
    :param PRIVMSG:
    :return: True if a !whatdeck query call is sent to the IRC server. Else false.
    """

    args = PRIVMSG.args

    # Seperate the N Cardname pairs from each other.
    # query = query.split(";") if ";" in query else query.split(",")
    # print query
    # For each N Cardname pair, seperate the N and the Cardname.
    # query = [(re.match("[0-9]*", query).strip(), re.match("[^0-9]*", query).strip()) for card in query]
    # print query

    # Turn table of (archetype, percentage) into string of N% archetype.

    probabilitiesTable = metagameDistribution(args)
    if probabilitiesTable:
        message = ", ".join("{1} {0}".format(archetype, percent) for archetype, percent in probabilitiesTable)
        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)
    else:
        message = "No decks in the format contain that card."
        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)


