class DeckError(Exception):
    def __init__(self, deck):
        self.deck = deck

    def __str__(self):
        return "No deck named \"{}\" found.".format(self.deck)

class CardError(Exception):
    def __init__(self, card):
        self.card = card

