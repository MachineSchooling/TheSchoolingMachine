# TheSchoolingMachine
Twitch IRC Bot for Magic: the Gathering

# About:
TheSchoolingMachine is is created and maintained by Twitch user MachineSchooling (Wally Wissner) to provide advanced features related to Magic: the Gathering to Twitch users. The project started in summer 2016, and new features are being actively introduced. TheSchoolingMachine is written in Python 2.7.

# Commands:
!whatdeck CARDNAME

Provides the probabilities of which deck archetype has been encountered based on the cards played. Assumes that all cards in a deck are equally likely to be played.

!running DECKNAME: CARDNAME

Provides the expected number of a card played in a deck archetype in both the maindeck and sideboard.

# Directory:
The bot object that interfaces with Twitch IRC is located in bot.py.

The commands that the bot will respond to from Twitch IRC users are located in commands.py.

The program to create the metagame dictionary (metagmaeDict.json) from MTGGoldfish.com's metagame data is located in metagame.py.

The program that provides the machinery for the "!whatdeck" and "!running" commands, as well as anything else that relies on metagame data, is located in metagameanalysis.py.

Custom exceptions related to cards or metagame archetypes are located in mtgexceptions.py.

The program that downloads card data from MTGJSON.com is located in mtgjson.py.

Required to run the bot, but not included here, is a file called private.py which contains the bot's login information.
