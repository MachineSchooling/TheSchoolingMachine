# -*- coding: utf-8 -*-

# Import standard modules.
import time
import socket
from datetime import datetime
# Import third party modules.
from parse import *
# Import custom modules.
import commands
import private
import metagame  # Needed to load/update the metagame master.
import mtgjson
from metagame import *  # Needed to operate the metagame master.
from updateable import Updateable


class Response(object):
    def __init__(self, bot, raw):
        self.bot = bot
        self.raw = raw

        self.parse_ping()
        self.parse_PRIVMSG()

    def parse_ping(self):
        if self.raw == "PING :tmi.twitch.tv":
            self.bot.pong()
            return True
        else:
            return False

    def parse_PRIVMSG(self):
        try:
            pattern = ":{NICK}!{NICK}@{NICK}.tmi.twitch.tv PRIVMSG #{CHAN} :{CONTENT}"
            parsed = parse(pattern, self.raw)
            PRIVMSG(bot=self.bot, NICK=parsed["NICK"], CHAN=parsed["CHAN"], CONTENT=parsed["CONTENT"])
            return True
        except TypeError:
            return False


class PRIVMSG(object):
    def __init__(self, bot, NICK, CHAN, CONTENT):
        self.bot = bot
        self.NICK = NICK
        self.CHAN = CHAN
        self.CONTENT = CONTENT

        self.bot.console(u"CHAN: {}, NICK: {}, CONTENT: {}".format(self.CHAN, self.NICK, self.CONTENT), mode="In")

        self.command, self.args = self.parse_command()

        if self.command:
            try:
                getattr(commands, self.command)(self)
            except AttributeError:
                pass

    def parse_command(self):
        content = self.CONTENT
        if len(content) < 2 or content[0] != '!' or content[1] == '_':
            command, args = None, None
        else:
            content = content.lstrip('!')
            try:
                command, args = content.split(' ', 1)
            except ValueError:
                command, args = content, None
        return command, args


class PersonList(object):
    # PersonList class is for maintaining lists of user, e.g., broadcaster channels or bot admins

    def __init__(self, file):
        self.file = file

        # Create file if it doesn't exist.
        with open(self.file, 'a+') as f:
            pass

        self.member_list = self.load()

    def __getitem__(self, item):
        return self.member_list[item]

    def __iter__(self):
        return iter(self.member_list)

    def load(self):
        with open(self.file, 'r') as f:
            memberlist = [member.strip('\n') for member in f]
        return memberlist

    def addperson(self, person):
        if person not in self.member_list:
            self.member_list.append(person)
            with open(self.file, 'a') as f:
                f.write(person + '\n')
            return True
        else:
            return False

    def delperson(self, person):
        self.member_list.remove(person)

        with open(self.file, 'w') as f:
            for member in self.member_list:
                f.write(member + '\n')
        return True


class Bot(object):
    # The main object that runs the bot, interfaces with the IRC, and calls helper programs.

    def __init__(self, HOST, PORT, NICK, PASS):
        self.quit = False

        print "="+"Loading".ljust(100, "=")

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
        self.CHANlist = PersonList("users.txt")
        for CHAN in self.CHANlist:
            self.join(CHAN)
            time.sleep(self.joinCOOL)

        # Bot administrators.
        self.administrators = PersonList("administrators.txt")

        # Launch the metagame object.
        self.metagame = Updateable(bot=self, updater=metagame.update, loader=metagame.load, filename="metagame.db")
        # Launch the card data object.
        self.carddata = Updateable(bot=self, updater=mtgjson.update, loader=mtgjson.load, filename="AllCards.json")

        print "="+"Online".ljust(100, "=")

        self.main_loop()

    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def console(self, message, mode="Out"):
        direction = "<<" if mode == "In" else ">>"
        print self.now(), direction, message

    def send(self, message):
        self.socket.send(message)

    def join(self, CHAN):
        self.send("JOIN #{}\r\n".format(CHAN))
        self.console("{} has joined {}'s channel".format(self.NICK, CHAN))

    def part(self, CHAN):
        self.send("PART #{}\r\n".format(CHAN))
        self.console("{} has departed from {}'s channel".format(self.NICK, CHAN))

    def chat(self, CHAN, message):
        self.send("PRIVMSG #{} :{}\r\n".format(CHAN, message))
        self.console("CHAN: {}, MESSAGE: {}".format(CHAN, message))

    def pong(self):
        self.send("PONG :tmi.twitch.tv\r\n")
        self.console("PONG")

    def main_loop(self):
        while not self.quit:
            # Check for updates.
            self.metagame.check_update()
            self.carddata.check_update()

            # Read next response from IRC.
            # Multiple PRIVMSGs may be sent by the server in one response, but are separated by newlines.
            responses = unicode(self.socket.recv(self.SIZE).decode("utf-8")).splitlines()
            for response in responses:
                Response(self, response)

            time.sleep(.1)

if __name__ == "__main__":
    TheSchoolingMachine = Bot(HOST="irc.chat.twitch.tv",
                              PORT=6667,
                              NICK="theschoolingmachine",
                              PASS=private.PASS
                              )
