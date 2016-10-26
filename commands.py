# Import standard modules.
import re
# Import custom modules.
from mtgexceptions import CardError
from mtgexceptions import DeckError
import metagame
from metagameanalysis import metagameDistribution
from metagameanalysis import metagameRunning
import mtgjson
from fuzzycard import nearestCardname
from fuzzycard import nearestDeckname

#FINISHED
def test(PRIVMSG):
    PRIVMSG.bot.chat(PRIVMSG.CHAN, "Hello, Twitch!")


#FINISHED
def commands(PRIVMSG):
    """
    Links to a list of commands.
    :return: True if a !commands call is sent to the IRC server. Else false.
    """
    message = "You can find a list of my commands here: https://github.com/MachineSchooling/TheSchoolingMachine#commands"
    PRIVMSG.bot.chat(PRIVMSG.CHAN, message)

#FINISHED
def about(PRIVMSG):
    """
    Links to a list of commands.
    :return: True if a !about call is sent to the IRC server. Else false.
    """
    message = "You can find out more about me here: " \
              "https://github.com/MachineSchooling/TheSchoolingMachine#theschoolingmachine"
    PRIVMSG.bot.chat(PRIVMSG.CHAN, message)


#FINISHED
def join(PRIVMSG):
    # Add command caller to list of users.
    user = PRIVMSG.NICK
    # If response is received on bot's channel add user to user list.
    if PRIVMSG.CHAN == PRIVMSG.bot.NICK:
        PRIVMSG.bot.CHANlist.addperson(user)
        PRIVMSG.bot.join(user)


#FINISHED
def part(PRIVMSG):
    # Remove command caller from list of users.
    user = PRIVMSG.NICK
    # If response is from the broadcaster of the channel remove the user from user list.
    if PRIVMSG.CHAN == PRIVMSG.NICK:
        PRIVMSG.bot.CHANlist.delperson(user)
        PRIVMSG.bot.part(user)



'''
#WORKING
def decklist(PRIVMSG):
    """
    Fetch a decklist page from MTGGoldfish based on the deck name given.
    :param PRIVMSG:
    :return:
    """

    deck = PRIVMSG.args

    if deck:
        deck = nearestDeckname(deck)
        message =

        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)
'''

#FINISHED
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
        card = nearestCardname(card)
        archetype = nearestDeckname(archetype)

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

    card = PRIVMSG.args
    card = nearestCardname(card)

    # Seperate the N Cardname pairs from each other.
    # query = query.split(";") if ";" in query else query.split(",")
    # print query
    # For each N Cardname pair, seperate the N and the Cardname.
    # query = [(re.match("[0-9]*", query).strip(), re.match("[^0-9]*", query).strip()) for card in query]
    # print query

    # Turn table of (archetype, percentage) into string of N% archetype.

    probabilitiesTable = metagameDistribution(card)
    if probabilitiesTable:
        message = "Weighted probabilities for {}: ".format(card)\
                  + ", ".join("{1} {0}".format(archetype, percent) for archetype, percent in probabilitiesTable)
        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)
    else:
        message = "No decks in the format contain that card."
        PRIVMSG.bot.chat(PRIVMSG.CHAN, message)

"""
#WORKING
def snip(PRIVMSG):
    pass
"""