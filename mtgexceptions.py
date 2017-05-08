# -*- coding: utf-8 -*-

class DeckError(Exception):
    def __init__(self, deck):
        self.deck = deck

    def __str__(self):
        return "No deck named \"{}\" found.".format(self.deck)

class CardError(Exception):
    def __init__(self, card):
        self.card = card

    def __str__(self):
        return "No card named \"{}\" found.".format(self.card)

class PatternError(Exception):
    def __init__(self, pattern):
        self.pattern = pattern

    def __str__(self):
        return self.pattern
