# Import standard modules.
import time
import datetime
import socket
from parse import *
# Import custom modules.
from metagame import *
import commands
import private
import mtgjson


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


class Bot(object):
    # The main object that runs the bot, interfaces with the IRC, and calls helper programs.

    def __init__(self, HOST, PORT, NICK, PASS):
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

        # Launch the metagame master object.
        self.masterfile = "metagamemaster.p"
        # If the object already exists load it. Otherwise, make a new object.
        try:
            self.console("Loading metagame master.")
            self.lastupdate = os.path.getmtime(self.masterfile)
            self.master = load_metagamemaster(self.masterfile)
            self.console("Metagame master loaded.")
        except OSError:
            self.console("Failed to load metagame master. Creating new metagame master.")
            self.master = MetagameMaster(self.masterfile)
            self.lastupdate = os.path.getmtime(self.masterfile)
            self.console("New metagame master created.")

        # Update the Magic card json.
        self.update_json()

        print "="+"Online".ljust(100, "=")

        self.main_loop()

    @staticmethod
    def now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    def pong(self, ):
        self.send("PONG :tmi.twitch.tv\r\n")
        self.console("PONG")


    #FINISHED
    def update_metagame(self, elapsed=60*60*24, start=0, end=24):
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
            self.console("Metagame object is updating.")
            self.master = MetagameMaster(self.masterfile)
            self.lastupdate = nowdate
            self.console("Metagame object updated.")
            return True
        else:
            return False

    def update_json(self):
        self.console("MTGJSON is updating.")
        mtgjson.update()
        self.console("MTGJSON updated.")

    def main_loop(self):
        while True:
            # See if metagame data needs to be updated and if so do it.
            self.update_metagame()

            # Read next response from IRC.
            # Ignore messages with weird unicode characters.
            try:
                # Multiple PRIVMSGs may be sent by the server in one response, but are separated by newlines.
                responses = unicode(self.socket.recv(self.SIZE).decode("utf-8")).splitlines()

                for response in responses:
                    Response(self, response)

            except UnicodeEncodeError:
                self.console("Unicode character not recognized.")


if __name__ == "__main__":
    TheSchoolingMachine = Bot(
        HOST="irc.chat.twitch.tv",
        PORT=6667,
        NICK="theschoolingmachine",
        PASS=private.PASS
    )
