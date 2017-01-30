# Import standard modules.
from parse import *
# Import custom modules.
from fuzzycard import ApproximateCardname, ApproximateDeckname


class _Command(object):
    def __init__(self, PRIVMSG):
        self.PRIVMSG = PRIVMSG
        self.command = PRIVMSG.command
        self.args = PRIVMSG.args
        self.bot = PRIVMSG.bot
        self.CHAN = PRIVMSG.CHAN

    def chat(self, message):
        return self.bot.chat(CHAN=self.CHAN, message=message)


    #Parsing format####################

    def first_arg(self):
        try:
            first, _ = self.args.split(" ", 1)
        except ValueError:
            first = None
        return first

    def parse_format(self, default=None):
        first_arg = self.first_arg().capitalize()
        return first_arg if first_arg in self.bot.master.formats else default


    #Parsing list strings####################

    def parse_list(self, listString):
        if ';' in listString:
            return listString.split(';')
        else:
            return listString.split(',')

    def parse_quantity_string(self, cardstring):
        stringlist = self.parse_list(cardstring)
        carddict = {self.parse_words(string): self.parse_number(string) for string in stringlist}
        return carddict

    def parse_cards_string(self, cardliststring):
        rawdict = self.parse_quantity_string(cardliststring)
        carddict = {unicode(ApproximateCardname(key)): rawdict[key] for key in rawdict}
        #carddict = {ApproximateCardname(key): rawdict[key] for key in rawdict}

        return carddict

    def parse_number(self, quantityliststring):
        try:
            numbers = [int(word.strip('x')) for word in quantityliststring.split() if
                       word.isdigit() or word.strip('x').isdigit()]
            return numbers[0]
        except IndexError:
            return 1

    def parse_words(self, quantityliststring):
        words = [word for word in quantityliststring.split() if not word.isdigit() and not word.strip('x').isdigit()]
        word = " ".join(words)
        return word



# Bot information commands.

class commands(_Command):
    # Displays the bot's commands page.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        message = "You can find a list of my commands here: " \
                  "https://github.com/MachineSchooling/TheSchoolingMachine#commands"
        self.chat(message)


class about(_Command):
    # Displays the bot's information page.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        message = "You can find out more about me here: " \
                  "https://github.com/MachineSchooling/TheSchoolingMachine#theschoolingmachine"
        self.chat(message)


class test(_Command):
    # Test to see if the bot is in the channel.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        message = "Hello, Twitch!"
        self.chat(message)


# Bot usage commands.

class join(_Command):
    # Add command caller to list of users.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        user = self.PRIVMSG.NICK
        # If response is received on bot's channel add user to user list.
        if self.PRIVMSG.CHAN == self.bot.NICK:
            if self.bot.CHANlist.addperson(user):
                message = "{} has joined {}'s channel.".format(self.bot.NICK, user)
            else:
                message = "{} has already joined {}'s channel.".format(self.bot.NICK, user)
            self.chat(message)


class part(_Command):
    # Remove command caller from list of users.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        user = self.PRIVMSG.NICK
        # If response is from the broadcaster of the channel remove the user from user list.
        if self.PRIVMSG.CHAN == self.PRIVMSG.NICK:
            self.bot.CHANlist.delperson(user)
            message = "{} will now depart {}'s channel.".format(self.bot.NICK, user)
            self.chat(message)
            self.bot.part(user)


# Metagame commands.

class whatdeck(_Command):
    # Deck archetype probabilities for encountered cards.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

        format_ = self.parse_format()

        if format_:
            pattern = "{format_} {cardstring}"
        else:
            pattern = "{cardstring}"
        parsed = parse(pattern, self.args)

        cardstring = parsed["cardstring"]
        carddict = self.parse_cards_string(cardstring)

        dictstring = ", ".join(str(carddict[cardname]) + ' ' + str(cardname) for cardname in carddict)

        format_ = format_ if format_ else u"Modern"

        probabilitiesTable = self.bot.master.whatdeck(format_=format_, carddict=carddict)

        if probabilitiesTable:
            message = "Weighted probabilities for {} in {}: ".format(dictstring, format_) \
                      + ", ".join("{} {}".format(percent, archetype) for percent, archetype in probabilitiesTable)
        else:
            message = "No {} decks contain {}.".format(format_, dictstring)

        self.chat(message)


class running(_Command):
    # How many copies of a card the deck archetype is playing.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        format_ = self.parse_format()

        if format_:
            pattern = "{format_} {archetype}: {cardname}"
        else:
            pattern = "{archetype}: {cardname}"
        parsed = parse(pattern, self.args)

        archetype = ApproximateDeckname(parsed['archetype'], format_)
        deckname = archetype.nearest()
        format_ = archetype.nearestformat()
        cardname = ApproximateCardname(parsed['cardname']).nearest()

        quantity = self.bot.master.running(format_=format_, archetype=deckname, cardname=cardname)

        rawmessage = "{} {} runs an average of {} in the maindeck and {} in the sideboard."
        message = rawmessage.format(format_, archetype, quantity["maindeck"], quantity["sideboard"])

        self.chat(message)


class decklist(_Command):
    # URL for deck archetype.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)
        format_ = self.parse_format()

        if format_:
            pattern = "{format_} {archetype}"
        else:
            pattern = "{archetype}"
        parsed = parse(pattern, self.args)

        archetype = ApproximateDeckname(parsed['archetype'], format_)
        deckname = archetype.nearest()
        format_ = archetype.nearestformat()

        url = self.bot.master[format_][deckname].url()

        rawmessage = "The most popular decklist for {} {} can be found here: {}"
        message = rawmessage.format(format_, deckname, url)
        self.chat(message)
