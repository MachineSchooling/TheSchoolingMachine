# Import standard modules.
import os
import time
import datetime
import socket
# Import custom modules.
from mtgexceptions import CardError
from mtgexceptions import DeckError
import metagame
import commands
import private


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
        self.parse(self.raw)

        # Output the parsed response to the console.
        toconsole = "response {} << NICK: {}, CHAN: {}, CONTENT: {}\r\n"
        print toconsole.format(self.bot.now(), self.NICK, self.CHAN, self.content)

    #FINISHED
    def parse(self, raw):
        """
        :param raw: Raw text sent by IRC server minus the terminating newline characters
        :return list: List elements correspond to NICK, CHAN, and content of the response.
        """
        # IRC server data is encapsulated by semicolons. Response content follows.
        data, content = [i for i in raw.lstrip(':').split(':', 1)]
        # Channel is what follows the '#' and has no spaces.
        _, CHAN = [i.strip() for i in data.split('#')]
        # NICK ends before the first '!'.
        NICK, _ = data.split('!')

        self.NICK, self.CHAN, self.content = NICK, CHAN, content

    #FINISHED
    def commandQ(self):
        # If the response doesn't begin with a '!' it is not a command.
        if self.content[0] != '!':
            return False
        else:
            # If the response is a command, the command call follows the '!' and ends before the first space.
            command_args = self.content.lstrip('!').split(' ', 1)

            # If the potential command has no arguments:
            if len(command_args) == 1:
                self.command = command_args[0]
            # If the potential command has arguments:
            else:
                self.command, self.args = command_args

        # See if the command call corresponds to a defined command.
        try:
            getattr(commands, self.command)(self)
            return True
        # If the response's text after the '!' and before the space isn't on the commands list, it is not a command.
        except AttributeError:
            return False


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
        self.memberlist.append(person)

        with open(self.file, 'a') as f:
            f.write(person + '\n')
            f.close()


    def delperson(self, person):
        self.memberlist.remove(person)

        with open(self.file, 'w') as f:
            for member in self.memberlist:
                f.write(member + '\n')
            f.close()



#FINISHED
# The main object that runs the bot, interfaces with the IRC, and calls helper programs.
class bot(object):
    def __init__(self, HOST, PORT, NICK, PASS):
        # Server id data.
        self.HOST = HOST # Host Server
        self.PORT = PORT # IRC Port
        # Bot id data.
        self.NICK = NICK # Twitch Username
        self.PASS = PASS # Twitch Password

        # Maximum response read size.
        self.SIZE = 2024

        # Network functions.
        self.socket = socket.socket()
        self.socket.connect((HOST, PORT))
        self.socket.send("PASS {}\r\n".format(PASS).encode("utf-8"))
        self.socket.send("NICK {}\r\n".format(NICK).encode("utf-8"))

        # Join each channel in list of users.
        self.CHANlist = personlist("users.txt")

        for CHAN in self.CHANlist:
            self.join(CHAN)

        print "\r\n"

        # Cooldown time between messages sent. 1 / Maximum messages per second. To avoid user spam and server bans.
        # 100messages/30seconds limit is iff you only message channels in which you are a moderator.
        self.COOL = 30.0 / 20.0

        # Last time metagame json file was updated.
        try:
            self.lastupdate = os.path.getmtime("metagameDict.json")
        except OSError:
            print "json file not found."

        # Start the bot.
        self.mainLoop()

    # Return the current date and time. Used for bot's log.
    def now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    # The bot joins the IRC channel CHAN.
    def join(self, CHAN):
        self.socket.send("JOIN #{}\r\n".format(CHAN).encode("utf-8"))
        print "{} has joined {}'s channel".format(self.NICK, CHAN)


    # The bot departs from the IRC channel CHAN.
    def part(self, CHAN):
        self.socket.send("PART #{}\r\n".format(CHAN).encode("utf-8"))
        print "{} has departed from {}'s channel".format(self.NICK, CHAN)


    #FINISHED
    def chat(self, CHAN, message):
        """
        Send a chat message to the server.
        :param message: String. The message to be sent.
        :return: None. A message is sent to the IRC server.
        """
        self.socket.send("PRIVMSG #{} :{}\r\n".format(CHAN, message).encode("utf-8"))
        print "message  {} >> {}\r\n".format(self.now(), message)


    #FINISHED
    def ping(self, response):
        """
        Checks IRC server response to see if it is a server ping. If it is a ping the bot pongs the server back.
        :param response: String received from the IRC server.
        :return: True if a pong is sent to the IRC server. Else false.
        """
        if response == "PING :tmi.twitch.tv\r\n":
            self.socket.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            print "message  {} >> PONG\r\n".format(self.now())
            return True
        else:
            return False


    #FINISHED
    def metagameupdate(self, magicFormat="modern", medium="online", elapsed=60*60*24, start=0, end=24):
        """
        Checks to see if metagameDict.json file is up to date and updates it if it isn't.
        :param elapsed: Seconds that have elapsed since last update needed to justify an update. (Default one day.)
        :param start: Beginning of range of hours in day to perform an update.
        :param end: End of range of hours in day to perform an update.
        :return: True if json file is updated. Else false.
        """
        # Get current date-time.
        nowdate = time.time()
        # Get current hour of day.
        nowhour = int(time.strftime("%H"))
        # If enough time has elapsed since last update and it is currently within updating hours, update.
        if (nowdate - self.lastupdate > elapsed) and (start < nowhour < end):
            print "json file is updating.\r\n"
            metagame.jsonupdate(magicFormat=magicFormat, medium=medium)
            self.lastupdate = nowdate
            print "json file updated.\r\n"
            return True
        else:
            return False


    def mainLoop(self):
        while True:

            # See if metagame data needs to be updated and if so do it.
            self.metagameupdate()


            # Read next response from IRC.
            # Ignore messages with weird unicode characters.
            try:
                response = self.socket.recv(self.SIZE).decode("utf-8")

            except UnicodeEncodeError:
                print "Unicode character not recognized.\r\n"
                continue


            # Only one of the below functions should message the IRC server per loop.
            # Otherwise the server will time the bot out for going over maximum messages per 30 seconds limit.

            # If the response is a ping, pong back.
            if self.ping(response):
                time.sleep(self.COOL)
                continue

            # See if the response is a PRIVMSG and if it is, see if it contains a command.
            if "PRIVMSG" in response:
                res = PRIVMSG(bot=self, string=response)
                # If the response contains a command, call it and message the IRC back the output.
                if res.commandQ():
                    time.sleep(self.COOL)
                    continue

            else:
                print "response {} << {}".format(self.now(), response)


TheSchoolingMachine = bot(
    HOST="irc.chat.twitch.tv",
    PORT=6667,
    NICK="theschoolingmachine",
    PASS=private.PASS
    )