# -*- coding: utf-8 -*-

import math
import os
import pathos.multiprocessing as mp
import re
import requests
import sqlite3
import sys
import time
from bs4 import BeautifulSoup
from collections import namedtuple
from collections import OrderedDict
from scipy.stats import hypergeom

sys.setrecursionlimit(1000000)

CardsRow = namedtuple("CardsRow", "cardname")
DecklistsRow = namedtuple("DecklistsRow", "id_deck, cardname, quantity, percent, sideboard")
FormatsRow = namedtuple("FormatsRow", "formatname")
MetagamesRow = namedtuple("MetagamesRow", "deckname, formatname, rawshare, url")
MetagamesRowNumbered = namedtuple("MetagamesRowNumbered", "id_deck, deckname, formatname, rawshare, url")


class MetagameMaster(object):
    def __init__(self, database="metagame.db"):
        self.database = database

        self.formats = ["Standard", "Modern", "Legacy", "Vintage", "Pauper"]

        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()

        self.create_function_LOG()
        self.create_function_EXP()
        self.create_aggregate_PROD()

    def update(self):
        open(self.database, 'w').close()  # Wipe database
        self.create_decklists()
        self.create_metagames()

        order = int(math.ceil(math.log(len(self.formats), 10)))  # Least power of 10 greater than the number of formats.
        metagame_rows = [MetagamesRowNumbered(id_deck=i * 10**order + id_format,
                                              deckname=mr.deckname,
                                              formatname=mr.formatname,
                                              rawshare=mr.rawshare,
                                              url=mr.url)
                         for id_format, format_ in enumerate(self.formats)
                         for i, mr in enumerate(self.scrape_metagame(format_))
                         ]
        pool = mp.Pool()
        decklist_rows = [decklist_row
                         for decklist in pool.imap(self.scrape_decklist, metagame_rows, chunksize=40)
                         for decklist_row in decklist
                         ]
        pool.close()
        pool.join()

        for row in metagame_rows:
            self.insert_to_metagames(id_deck=row.id_deck,
                                     formatname=row.formatname,
                                     deckname=row.deckname,
                                     rawshare=row.rawshare,
                                     url=row.url)

        for row in decklist_rows:
            self.insert_to_decklists(id_deck=row.id_deck,
                                     cardname=row.cardname,
                                     quantity=row.quantity,
                                     percent=row.percent,
                                     sideboard=row.sideboard)

        self.connection.commit()

    # Scraping #########################################################################################################

    def scrape_metagame(self, formatname):
        url = "https://www.mtggoldfish.com/metagame/{}/full#online".format(formatname)
        page = requests.get(url).content
        fullsoup = BeautifulSoup(page, "lxml")
        soup = fullsoup.find("div", class_="metagame-list-full-content")

        decklists = []

        for decklist_tile in soup.find_all(class_="archetype-tile"):
            try:
                rawshare = self.string_try_to_float(
                    decklist_tile.find(class_="percentage col-freq").contents[0].strip('\n')
                )
                url_short = decklist_tile.find('a', class_="card-image-tile-link-overlay")["href"]
                url = "https://www.mtggoldfish.com" + url_short
                deckname = decklist_tile.find('a', href=url_short + "#online").contents[0]

                decklists.append(MetagamesRow(deckname, formatname, rawshare, url))

            except TypeError:
                pass

        print decklists
        return decklists

    def scrape_decklist(self, decklist_row):
        url = decklist_row.url

        page = requests.get(url).content
        fullsoup = BeautifulSoup(page, "lxml")
        soup = fullsoup.find('div', class_="archetype-details")

        cards = []

        for card_type_subsection in soup.find_all('div', class_="archetype-breakdown-section"):
            for featured in card_type_subsection.find_all('div', class_="archetype-breakdown-featured-card"):
                try:
                    cardname = self.clean_name(featured.find('img')['alt'])
                    percent_quantity = featured.find('p', class_="archetype-breakdown-featured-card-text").contents[0]
                    percent = self.clean_number(re.search("[0-9]+%", percent_quantity).group(0))
                    quantity = int(self.clean_number(re.search("[0-9]+x", percent_quantity).group(0)))
                    sideboard = card_type_subsection.find('h4').contents[0] == "Sideboard"
                    cards.append(DecklistsRow(decklist_row.id_deck, cardname, quantity, percent, sideboard))
                except AttributeError:
                    pass
            for unfeatured in card_type_subsection.find_all('tr'):
                try:
                    cardname = self.clean_name(unfeatured.find('a').contents[0])
                    percent = self.clean_number(unfeatured.find('td', class_="deck-col-frequency").contents[0])
                    quantity = int(self.clean_number(unfeatured.find('td', class_="deck-col-qty").contents[0]))
                    sideboard = card_type_subsection.find('h4').contents[0] == "Sideboard"
                    cards.append(DecklistsRow(decklist_row.id_deck, cardname, quantity, percent, sideboard))
                except AttributeError:
                    pass

        print cards
        return cards

    # Formatting #######################################################################################################

    @staticmethod
    def string_try_to_float(x):
        # Converts MTGGoldfish reported data into floats if they're numbers.
        try:
            return float(x)
        except ValueError:
            try:
                return float(x.strip('%')) / 100
            except ValueError:
                return x

    @staticmethod
    def clean_name(name):
        # Takes a cardname with art specification and returns just the card's name. (Removes everything in parentheses.)
        regex_del = "\(([^\)]+)\)"
        return str(re.sub(regex_del, "", name).strip())

    def clean_number(self, number):
        # Cleans up whitespace and NUMx from MTGGoldfish HTML and converts to float.
        return self.string_try_to_float(number.strip().strip('x'))

    @staticmethod
    def percent(num, decimals=0):
        """
        :param num: Float to be rewritten as a percentage.
        :param decimals: Number of decimals to display.
        :return: 'N%' string.
        """
        return "{0:.{1}f}%".format(num * 100, decimals)

    @staticmethod
    def humanform(number, decimals=1):
        """
        :param number: Float to be rewritten with specified significant digits.
        :param decimals: Number of decimals to display.
        :return: 'N.M' string.
        """
        if number == int(number):
            return str(number)
        else:
            return "{0:.{1}f}".format(number, decimals)

    def plausibile(self, intable, maxrows=5, threshold=.05):
        """
        :param intable: Table of archetypes and associated probabilities.
        :param maxrows: Maximum number of archetypes to display.
        :param threshold: Minimum likelihood to display.
        :return: outtable is intable rows which satisfy max and threshold restrictions
        """
        outtable = [(self.percent(probability), archetype) for probability, archetype in intable[:maxrows] if
                    probability > threshold]
        return outtable

    # SQL setup ########################################################################################################

    def create_function_LOG(self):
        self.connection.create_function("LOG", 1, math.log)

    def create_function_EXP(self):
        self.connection.create_function("EXP", 1, math.exp)

    def create_aggregate_PROD(self):
        class P(object):
            def __init__(self):
                self.prod = 1

            def step(self, value):
                self.prod *= value

            def finalize(self):
                return self.prod

        self.connection.create_aggregate("PROD", 1, P)

    def create_aggregate_THISDECK(self, carddict):
        def hg(cardname, quantity, percent):
            try:
                actualsuccesses = carddict[cardname]
                decksize = 60
                successdraws = quantity
                cardsdrawn = sum(carddict.values())
                return hypergeom.pmf(k=actualsuccesses, M=decksize, n=successdraws, N=cardsdrawn) * percent
            except KeyError:
                return 0

        class TD(object):
            def __init__(self):
                self.prod = 0
                self.accounted = set()

            def step(self, rawshare, cardname, quantity, percent):
                if cardname in carddict:
                    self.accounted.add(cardname)
                    if self.prod is 0:
                        self.prod = rawshare
                    self.prod *= hg(cardname, quantity, percent)

            def finalize(self):
                if self.accounted == set(carddict.keys()):
                    return self.prod
                else:
                    return 0

        self.connection.create_aggregate("THISDECK", 4, TD)

    def create_decklists(self):
        command = """
        CREATE TABLE decklists (
        id INTEGER PRIMARY KEY,
        id_deck INTEGER,
        cardname VARCHAR(100),
        quantity INTEGER,
        percent FLOAT,
        sideboard BOOL
        )
        """
        self.cursor.execute(command)

    def create_metagames(self):
        command = """
        CREATE TABLE metagames (
        id INTEGER PRIMARY KEY,
        id_deck INTEGER,
        formatname VARCHAR(100),
        deckname VARCHAR(100),
        rawshare FLOAT,
        url VARCHAR(100)
        )
        """
        self.cursor.execute(command)

    def insert_to_decklists(self, id_deck, cardname, quantity, percent, sideboard):
        command = """
        INSERT INTO decklists (id_deck, cardname, quantity, percent, sideboard)
        VALUES (?,?,?,?,?)
        """
        self.cursor.execute(command, [id_deck, cardname, quantity, percent, sideboard])

    def insert_to_metagames(self, id_deck, formatname, deckname, rawshare, url):
        command = """
        INSERT INTO metagames (id_deck, formatname, deckname, rawshare, url)
        VALUES (?,?,?,?,?)
        """
        self.cursor.execute(command, [id_deck, formatname, deckname, rawshare, url])

    # SQL queries ######################################################################################################

    def decknames(self, formatname=None, show_formats=False):
        if formatname:
            formatname_specification = "WHERE formatname = ?"
            args = [formatname]
        else:
            formatname_specification = ""
            args = []

        command = """
        SELECT DISTINCT deckname, formatname
        FROM metagames
        {}
        ORDER BY rawshare DESC
        """.format(formatname_specification)
        self.cursor.execute(command, args)

        result = self.cursor.fetchall()

        if show_formats:
            output = OrderedDict()
            for i in result:
                output[i[0]] = i[1]
        else:
            output = [i[0] for i in result]

        return output

    def whatdeck(self, formatname, carddict):
        self.create_aggregate_THISDECK(carddict)

        table_thisdeck = """
        SELECT d.id_deck, deckname, THISDECK(rawshare, cardname, quantity, percent) AS thisdeck
        FROM decklists d
        JOIN metagames m
        ON d.id_deck = m.id_deck
        WHERE sideboard = 0 AND formatname = ?
        GROUP BY d.id_deck
        """

        command = """
        SELECT SUM(thisdeck) / (SELECT SUM(thisdeck) FROM ({})) AS probability, deckname
        FROM({})
        GROUP BY deckname
        HAVING probability > .05
        ORDER BY probability DESC
        LIMIT 5
        """.format(table_thisdeck, table_thisdeck)

        self.cursor.execute(command, [formatname, formatname])
        result = self.cursor.fetchall()
        return self.plausibile(result)

    def running(self, formatname, deckname, cardname):
        command = """
        SELECT SUM(ev * rawshare) / SUM(rawshare), sideboard
        FROM(
            SELECT SUM(CASE WHEN cardname = ? THEN d.quantity * d.percent ELSE 0 END) AS ev, rawshare, sideboard
            FROM decklists d
            JOIN metagames m
            ON m.id_deck = d.id_deck
            WHERE formatname = ? AND deckname = ?
            GROUP BY d.id_deck, sideboard
            )
        GROUP BY sideboard
        """
        self.cursor.execute(command, [cardname, formatname, deckname])
        result = self.cursor.fetchall()

        outdict = {'maindeck': '0', 'sideboard': '0'}
        for board in result:
            outdict[('maindeck', 'sideboard')[board[1]]] = self.humanform(board[0])  # board[1] determines the board

        return outdict

    def decklist(self, deckname, formatname=None):
        if formatname:
            format_restriction = "AND formatname = ?"
            args = [deckname, formatname]
        else:
            format_restriction = ""
            args = [deckname]

        command = """
        SELECT m.url
        FROM metagames m
        JOIN decklists d
        ON d.id_deck = m.id_deck
        WHERE deckname = ? {}
        ORDER BY m.rawshare DESC
        LIMIT 1
        """.format(format_restriction)
        self.cursor.execute(command, args)
        result = self.cursor.fetchall()
        return result[0][0]


def update():
    master = MetagameMaster()
    master.update()


def load():
    master = MetagameMaster()
    return master


if __name__ == "__main__":
    m = MetagameMaster()

    update = False

    if update:
        t0 = time.time()
        m.update()
        t1 = time.time()
        print "timing:", t1 - t0

    print "formats:", m.formats
    print "decknames:", m.decknames()
    print "decknames:", m.decknames(show_formats=True)
    print "decknames standard:", m.decknames("Standard")
    print "decklist:", m.decklist(u"Dredge")
    print "decklist:", m.decklist(deckname=u"Dredge", formatname="Vintage")
    print "running:", m.running("Modern", u"Dredge", "Ancient Grudge")
    print "running:", m.running("Modern", "Affinity", "Etched Champion")
    print "running:", m.running("Modern", "Abzan", "Tarmogoyf")
    print "whatdeck:", m.whatdeck("Modern", {"Death's Shadow": 1, "Bloodstained Mire": 2})
    print "whatdeck:", m.whatdeck("Modern", {"Eldrazi Temple": 1, "Chalice of the Void": 2})
    print "whatdeck:", m.whatdeck("Modern", {"Tarmogoyf": 2, "Forest": 1})
