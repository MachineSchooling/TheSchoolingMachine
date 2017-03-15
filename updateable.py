import time
import os


class Updateable(object):
    def __init__(self, bot, updater, loader, filename, elapsed=60 * 60 * 24, start=5, end=6):
        self.bot = bot
        self.updater = updater #updates file
        self.loader = loader #returns object
        self.filename = filename #name of file where object data is stored
        self.elapsed = elapsed #how often to update (in seconds)
        self.start = start #beginning time of day where update is allowed
        self.end = end #ending time of day when update is allowed

        self.content = self.load()

    def check_update(self):
        allowed = self.allowed()
        if allowed:
            self.bot.console("{} is updating.".format(self.filename))
            self.updater(self.filename)
            self.loader(self.filename)
            self.bot.console("{} has updated".format(self.filename))
        return allowed

    def last_update(self):
        return os.path.getmtime(self.filename)

    def allowed(self):
        nowdate = time.time()
        nowhour = int(time.strftime("%H"))
        return (nowdate - self.last_update() > self.elapsed) and (self.start < nowhour < self.end)

    def load(self):
        try:
            self.bot.console("{} is loading.".format(self.filename))
            return self.loader()

        except IOError:
            self.bot.console("{} failed to load. Rebuilding.".format(self.filename))
            self.updater()
            return self.loader()


