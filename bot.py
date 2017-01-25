#!/usr/bin/python
# -*- coding: utf-8 -*-


# Import standard modules.
import os
import time
import datetime
import socket
import cPickle
# Import custom modules.
from metagame import *
import commands
import private
import mtgjson


#FINISHED
# PRIVMSG (private message) object which unpacks the data from a received IRC message.
class PRIVMSG(object):
    def __init__(self, bot, string):
        """
        :param bot: Bot from which the PRIVMSG is received.
        :param string: Raw text sent by IRC server including the terminating newline characters.
        """
        # Bot which is processing the PRIVMSG. PRIVMSG uses the bot's .chat method.
        self.bot = bot
        # Raw is of the form ":NICK!NICK@NICK.tmi.twitch.tv PRIVMSG #CHAN :content"
        self.raw = string.strip('\r\n')
        # Parse the raw response to find the NICK, CHAN, and content of the response.
        self.NICK, self.CHAN, self.content = self.parseOrigin()
        # Output the parsed response to the console.
        toconsole = "response {} << CHAN: {}, NICK: {}, CONTENT: {}\r\n"
        print toconsole.format(self.bot.now(), self.CHAN, self.NICK, self.content)

        # Determine if the response contains a command.
        self.command, self.args = self.parseCommand()
        # If the response does contain a command, execute it.
        if self.command:
            try:
                getattr(commands, self.command)(self)
            except AttributeError:
                pass

    #FINISHED
    def parseOrigin(self):
        """
        :param raw: Raw text sent by IRC server minus the terminating newline characters
        :return list: List elements correspond to NICK, CHAN, and content of the response.
        """
        try:
            # IRC server data is encapsulated by semicolons. Response content follows.
            data, content = [i for i in self.raw.lstrip(':').split(':', 1)]
            # Channel is what follows the '#' and has no spaces.
            _, CHAN = [i.strip() for i in data.split('#')]
            # NICK ends before the first '!'.
            NICK, _ = data.split('!')

            return NICK, CHAN, content

        except ValueError:
            print "ValueError: {}".format(self.raw)

    #FINISHED
    def parseCommand(self):
        # Check if the response is in the format of a command.

        content = self.content
        if len(content) < 2 or content[0] != '!' or content[1] == '_':
            command, args = None, None
        else:
            content = content.lstrip('!')
            try:
                command, args = content.split(' ', 1)
            except ValueError:
                command, args = content, None
        return command, args



#FINISHED
# personlist class is for maintaining lists of user, e.g., broadcaster channels or bot admins
class personlist(object):
    def __init__(self, file):
        self.file = file
        self.memberlist = self.load(self.file)

    def __getitem__(self, item):
        return self.memberlist[item]

    def __iter__(self):
        return iter(self.memberlist)

    def load(self, document):
        with open(self.file, 'r') as f:
            memberlist = [member.strip('\n') for member in f]
            f.close()
        return memberlist

    def addperson(self, person):
        if person not in self.memberlist:
            self.memberlist.append(person)
            with open(self.file, 'a') as f:
                f.write(person + '\n')
                f.close()
            return True
        else:
            return False

    def delperson(self, person):
        self.memberlist.remove(person)

        with open(self.file, 'w') as f:
            for member in self.memberlist:
                f.write(member + '\n')
            f.close()
        return True


#FINISHED
# The main object that runs the bot, interfaces with the IRC, and calls helper programs.
class Bot(object):
    def __init__(self, HOST, PORT, NICK, PASS):
        # Server id data.
        self.HOST = HOST  # Host Server
        self.PORT = PORT  # IRC Port
        # Bot id data.
        self.NICK = NICK  # Twitch Username
        self.PASS = PASS  # Twitch Password

        # Maximum response read size.
        self.SIZE = 2**20

        # Network functions.
        self.socket = socket.socket()
        self.socket.connect((HOST, PORT))
        self.send("PASS {}\r\n".format(PASS))
        self.send("NICK {}\r\n".format(NICK))

        # Cooldown time between messages sent. 1 / Maximum messages per second. To avoid user spam and server bans.
        # 100messages/30seconds limit is iff you only message channels in which you are a moderator.
        # 20messages/30seconds otherwise.
        self.messageCOOL = 30.0 / 20.0

        # Cooldown time between joins sent. 1 / Maximum joins per second. To avoid server bans.
        # 50joins/15seconds.
        self.joinCOOL = 15.0 / 50.0

        # Join each channel in list of users.
        self.CHANlist = personlist("users.txt")
        for CHAN in self.CHANlist:
            self.join(CHAN)
            time.sleep(self.joinCOOL)

        # Launch the metagame master object.
        self.masterfile = "metagamemaster.p"
        # If the object already exists load it. Otherwise, make a new object.
        try:
            print self.now(), ">>", "Loading metagame master.\r\n"
            self.lastupdate = os.path.getmtime(self.masterfile)
            self.master = loadMetagameMaster(self.masterfile)
            print self.now(), ">>", "Metagame master loaded.\r\n"
        except OSError:
            print self.now(), ">>", "Failed to load metagame master. Creating new metagame master.\r\n"
            self.master = metagamemaster(self.masterfile)
            self.lastupdate = os.path.getmtime(self.masterfile)
            print self.now(), ">>", "New metagame master created.\r\n "

        # Update the Magic card json.
        self.json_update()

        self.mainLoop()

    @staticmethod
    def now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def send(self, message):
        #self.socket.send(message.encode("utf-8"))
        self.socket.send(message)

    def join(self, CHAN):
        self.send("JOIN #{}\r\n".format(CHAN))
        print "{} has joined {}'s channel\r\n".format(self.NICK, CHAN)

    def part(self, CHAN):
        self.send("PART #{}\r\n".format(CHAN))
        print "{} has departed from {}'s channel\r\n".format(self.NICK, CHAN)

    def chat(self, CHAN, message):
        self.send("PRIVMSG #{} :{}\r\n".format(CHAN, message))
        print "message  {} >> {}\r\n".format(self.now(), message)

    def ping(self, response):
        #Checks IRC server response to see if it is a server ping. If it is a ping the bot pongs the server back.
        if response == "PING :tmi.twitch.tv\r\n":
            self.send("PONG :tmi.twitch.tv\r\n")
            print "message  {} >> PONG\r\n".format(self.now())
            return True
        else:
            return False


    #FINISHED
    def metagameupdate(self, elapsed=60*60*24, start=0, end=24):
        """
        Checks to see if the metagame object is up to date and updates it if it isn't.
        :param elapsed: Seconds that have elapsed since last update needed to justify an update. (Default one day.)
        :param start: Beginning of range of hours in day to perform an update.
        :param end: End of range of hours in day to perform an update.
        :return: True if metagame object is updated. Else false.
        """
        # Get current date-time.
        nowdate = time.time()
        # Get current hour of day.
        nowhour = int(time.strftime("%H"))
        # If enough time has elapsed since last update and it is currently within updating hours, update.
        if (nowdate - self.lastupdate > elapsed) and (start < nowhour < end):
            print self.now(), ">>", "Metagame object is updating.\r\n"
            self.master = metagamemaster(self.masterfile)
            self.lastupdate = nowdate
            print self.now(), ">>", "Metagame object updated.\r\n"
            return True
        else:
            return False

    def json_update(self):
        print self.now(), ">>", "MTGJSON is updating.\r\n"
        mtgjson.json_update()
        print self.now(), ">>", "MTGJSON updated.\r\n"

    def mainLoop(self):
        while True:
            # See if metagame data needs to be updated and if so do it.
            self.metagameupdate()

            # Read next response from IRC.
            # Ignore messages with weird unicode characters.
            try:
                # Multiple PRIVMSGs may be sent by the server in one response, but are separated by newlines.
                responses = unicode(self.socket.recv(self.SIZE).decode("utf-8")).splitlines()

                for response in responses:
                    # Only one of the below functions should message the IRC server per loop to avoid server ban.

                    # If the response is a ping, pong back.
                    if self.ping(response):
                        time.sleep(self.messageCOOL)
                        continue

                    # See if the response is a PRIVMSG and if it is, see if it contains a command.
                    if "PRIVMSG" in response:
                        res = PRIVMSG(bot=self, string=response)
                        # If the response contains a command, call it and message the IRC back the output.
                        if res.command:
                            time.sleep(self.messageCOOL)
                            continue
                    else:
                        print "response {} << {}".format(self.now(), response)

            except UnicodeEncodeError:
                print "Unicode character not recognized.\r\n"


if __name__ == "__main__":
    TheSchoolingMachine = Bot(
        HOST="irc.chat.twitch.tv",
        PORT=6667,
        NICK="theschoolingmachine",
        PASS=private.PASS
    )
