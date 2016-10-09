# Uses python-levenshtein module implicitly.
from fuzzywuzzy import fuzz

#WORKING
def cardPopularity(cardname):


# If card name match ratios are tied, pick the card with the most metagame share.
(ratio, metagameshare, cardname)


# The name of a legendary card without the epithet.
def legendname(cardname):
    return cardname.split(',')[0]

#WORKING
def nearestCardname(query, optionlist, method='ratio'):
    """
    :param query: String that may or may not be an actual Magic card's name.
    :param optionlist: List of all Magic card names.
    :return: The name of the actual Magic card with the name closest to the input string.
    """
    # (Ratio method output, Card name)
    def ratiopair(query, option):
        query = query.lower()
        option = option.lower()
        return (getattr(fuzz, method)(query, option), option)

    ratingslist = [max([ratiopair(query, option), ratiopair(query, legendname(option))]) for option in optionlist]
    #return max(ratingslist)[1]
    return ratingslist





print fuzz.ratio('keiga', 'Keiga, the Tide Star')
print fuzz.ratio('keiga', legendname('Keiga, the Tide Star'))

print fuzz.ratio('kaiga', 'Keiga, the Tide Star')
print fuzz.ratio('kaiga', legendname('Keiga, the Tide Star'))

print fuzz.ratio('Teiga', 'Taiga')
print fuzz.ratio('Teiga', legendname('Keiga, the Tide Star'))

print closestmatch('tron', ['Mono U Tron', "GR Tron", 'Fish', "Eldrazi"])

print closestmatch('keiga', ['Keiga, the Tide Star', "Keira", 'Fish', "Eldrazi"], 'partial_ratio')

print closestmatch('keiga', ['Keiga, the Tide Star', "Keira", 'Fish', "Eldrazi"])

print closestmatch('Skite', ['Spellskite', "Skittering Giberer", 'Fish', "Eldrazi"])


print closestmatch('Skite', ['Spellskite', "Skittering Giberer", 'Fish', "Eldrazi"], 'partial_ratio')

print legendname('Keiga, the Tide Star')
print legendname('Lightning Bolt')