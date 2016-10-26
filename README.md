# TheSchoolingMachine
TheSchoolingMachine is an IRC bot created and maintained by Twitch user MachineSchooling (Wally Wissner) to provide advanced features related to Magic: the Gathering to Twitch users. The project started in summer 2016, and new features are being actively introduced. TheSchoolingMachine is written in Python 2.7.

# Commands:

!join

Type this command in TheSchoolingMachine's Twitch chat (https://www.twitch.tv/machineschooling) to have the bot join your channel and have its commands be accessable from your chat.

!part

Type this command in your channel's chat and the bot will stop responding to commands issued from your chat.

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

Inexact user input is handled in fuzzycard.py.

Required to run the bot, but not included here, is a file called private.py which contains the bot's login information.

Required to run the bot, but not included here, is a file called users.txt which contains the bot's active user list.
