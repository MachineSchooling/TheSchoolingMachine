# -*- coding: utf-8 -*-

# Import standard modules.
from parse import *
import requests
# Import custom modules.
from fuzzycard import ApproximateCardname, ApproximateDeckname

class _Command(object):
    def __init__(self, PRIVMSG, min_privilege="Viewer"):
        self.PRIVMSG = PRIVMSG
        self.command = PRIVMSG.command
        self.args = PRIVMSG.args
        self.bot = PRIVMSG.bot
        self.CHAN = PRIVMSG.CHAN
        self.NICK = PRIVMSG.NICK
        self.min_privilege = min_privilege

        try:
            self.main()
        except TypeError:
            # Type error corresponds to malformed parse pattern.
            self.chat(self.error_message())

    def chat(self, message):
        return self.bot.chat(CHAN=self.CHAN, message=message)

    def console(self, message, mode='Out'):
        return self.bot.console(message=message, mode=mode)

    def pattern(self):
        return ""

    def main(self):
        pass

    def parsed(self, arg=None):
        parsed = parse(self.pattern(), self.args)
        if arg:
            return parsed[arg]
        else:
            return parsed

    def error_pattern(self):
        return self.pattern()

    def error_message(self):
        rawmessage = "Could not understand command. Command should be formatted as: !{} {}"
        return rawmessage.format(type(self).__name__, self.error_pattern())

    #INCOMPLETE
    def user_privileges(self):
        privileges = {}
        privileges["BotAdministrator"] = self.NICK in self.bot.administrators
        privileges["Broadcaster"] = self.NICK == self.CHAN
        privileges["Moderator"] = False #self.NICK in self.CHAN.moderators
        privileges["Subscriber"] = False
        privileges["Follower"] = False
        privileges["Viewer"] = True
        return privileges

    #Parsing format#####################################################################################################

    def first_arg(self):
        try:
            first, _ = self.args.split(" ", 1)
        except ValueError:
            first = self.args
        return first

    def parse_format(self, default=None):
        first_arg = self.first_arg().capitalize()
        format_ = first_arg if first_arg in self.bot.metagame.content.formats else default
        return format_

    #Parsing list strings###############################################################################################

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
        carddict = {unicode(ApproximateCardname(bot=self.bot, target=key)): rawdict[key] for key in rawdict}
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



#Bot information commands###############################################################################################

class commands(_Command):
    # Displays the bot's commands page.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def main(self):
        message = "You can find a list of my commands here: " \
                  "https://github.com/MachineSchooling/TheSchoolingMachine#commands"
        self.chat(message)


class about(_Command):
    # Displays the bot's information page.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def main(self):
        message = "You can find out more about me here: " \
                  "https://github.com/MachineSchooling/TheSchoolingMachine#theschoolingmachine"
        self.chat(message)


class test(_Command):
    # Test to see if the bot is in the channel.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def main(self):
        message = "Hello, Twitch!"
        self.chat(message)


#Bot usage commands#####################################################################################################

class join(_Command):
    # Add command caller to list of users.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def main(self):
        # If response is received on bot's channel add user to user list.
        if self.PRIVMSG.CHAN == self.bot.NICK:

            if self.bot.CHANlist.addperson(self.NICK):
                self.bot.join(self.NICK)
                message = "{} has joined {}'s channel.".format(self.bot.NICK, self.NICK)

            else:
                message = "{} has already joined {}'s channel.".format(self.bot.NICK, self.NICK)

            self.chat(message)


class part(_Command):
    # Remove command caller from list of users.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def main(self):
        user = self.PRIVMSG.NICK
        # If response is from the broadcaster of the channel remove the user from user list.
        if self.PRIVMSG.CHAN == self.PRIVMSG.NICK:
            self.bot.CHANlist.delperson(user)
            message = "{} will now depart {}'s channel.".format(self.bot.NICK, user)
            self.chat(message)
            self.bot.part(user)


#Metagame commands######################################################################################################

class whatdeck(_Command):
    # Deck archetype probabilities for encountered cards.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def pattern(self):
        format_ = self.parse_format()

        if format_:
            pattern = "{format} {cardstring}"
        else:
            pattern = "{cardstring}"

        return pattern

    def error_pattern(self):
        cardlist_pattern = "{N1 card1}, {N2 card2},..."

        format_ = self.parse_format()
        if format_:
            return "{format} " + cardlist_pattern
        else:
            return cardlist_pattern

    def main(self):
        parsed = self.parsed()
        cardstring = parsed["cardstring"]
        carddict = self.parse_cards_string(cardstring)
        dictstring = ", ".join(str(carddict[cardname]) + ' ' + str(cardname) for cardname in carddict)
        format_ = self.parse_format(default="Modern")
        probabilities_table = self.bot.metagame.content.whatdeck(formatname=format_, carddict=carddict)

        if probabilities_table:
            message = "Weighted probabilities for {} in {}: ".format(dictstring, format_) \
                      + ", ".join("{} {}".format(percent, archetype) for percent, archetype in probabilities_table)
        else:
            message = "No {} decks contain {}.".format(format_, dictstring)

        self.chat(message)


class running(_Command):
    # How many copies of a card the deck archetype is playing.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def pattern(self):
        format_ = self.parse_format()

        if format_:
            pattern = "{format} {archetype}: {cardname}"
        else:
            pattern = "{archetype}: {cardname}"

        return pattern

    def main(self):
        parsed = parse(self.pattern(), self.args)
        format_ = self.parse_format(default=None)
        archetype = ApproximateDeckname(bot=self.bot, target=parsed['archetype'], format_=format_)
        deckname = archetype.nearest()
        format_ = archetype.nearest_format()
        cardname = ApproximateCardname(bot=self.bot, target=parsed['cardname']).nearest()
        quantity = self.bot.metagame.content.running(formatname=format_, deckname=deckname, cardname=cardname)

        rawmessage = "{} {} runs an average of {} {} in the maindeck and {} in the sideboard."
        message = rawmessage.format(format_, archetype, quantity["maindeck"], cardname, quantity["sideboard"])

        self.chat(message)


class decklist(_Command):
    # URL for deck archetype.
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def pattern(self):
        format_ = self.parse_format()

        if format_:
            pattern = "{format} {archetype}"
        else:
            pattern = "{archetype}"

        return pattern

    def main(self):
        format_ = self.parse_format(None)

        archetype = ApproximateDeckname(bot=self.bot, target=self.parsed('archetype'), format_=format_)
        deckname = archetype.nearest()
        format_ = archetype.nearest_format()

        url = self.bot.metagame.content.decklist(deckname=deckname, formatname=format_)

        rawmessage = "The most popular decklist for {} {} can be found here: {}"
        message = rawmessage.format(format_, deckname, url)
        self.chat(message)


#Utility commands#######################################################################################################

class pronounce(_Command):
    def __init__(self, PRIVMSG):
        _Command.__init__(self, PRIVMSG)

    def pattern(self):
        pattern = "{word}"
        return pattern

    def main(self):
        word = self.parsed("word").lower()

        url = "http://dictionary.cambridge.org/us/pronunciation/english/" + word.replace(' ', '-')

        if requests.get(url).url == url:
            message = "Pronunciation for \"{}\" can be found at: {}".format(word, url)
        else:
            message = "No pronunciation for \"{}\" found.".format(word)

        self.chat(message)
