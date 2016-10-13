# Uses python-levenshtein module implicitly.
from fuzzywuzzy import fuzz

import mtgjson


import json
f = open("metagameDict.json", 'r')
metagameDict = json.loads(f.read())
f.close()


#FINISHED
def flatten(inlist, level=float('inf')):
    def isFlat(inlist):
        for element in inlist:
            if isinstance(element, list):
                return False
        return True

    def makeFlatter(inlist):
        outlist = []
        for item in inlist:
            if isinstance(item, list):
                outlist += item
            else:
                outlist.append(item)
        return outlist

    flatter = makeFlatter(inlist)
    return flatter if isFlat(flatter) or not level-1 else flatten(flatter, level-1)


#WORKING
# If card name match ratios are tied, pick the card with the most metagame share.
# (ratio, metagameshare, cardname)
def cardPopularity(cardname):
    pass

#FINISHED
def nearestString(query, options, transformations, method):
    """
    :param query: String that may or may not be an actual Magic card's name.
    :param options: List of all Magic card names.
    :param transformations: List of transformations of the options to compare with query string. Use best among ratios.
    :param method: String name of fuzzywuzzy ratio method to use.
    :return: The string among the options closest to the input string.
    """
    def ratiopair(query, option, transformed):
        """
        :param option: String element of optionlist.
        :param transformed: String transformed from option by a transformation in transformations.
        :return: Tuple (Ratio method output, option)
        """
        # When cardPopularity is done, it will be the second element of this tuple.
        return (getattr(fuzz, method)(query.lower(), transformed.lower()), option)

    # List of transformations on the options.
    def comparelist(option):
        """
        :param option: String element of optionlist.
        :return:
        """
        # For each transformation function, compute the transformed strings.
        transformedlist = flatten([transformation(option) for transformation in transformations])

        # For each transformed string, compare that string with the query string.
        return [ratiopair(query, option, option)]\
               + [ratiopair(query, option, transformed) for transformed in transformedlist]

    ratingslist = [max(comparelist(option)) for option in options]
    return max(ratingslist)[1]


#FINISHED
def nearestDeckname(query):

    archetypes = [metagame for metagame in metagameDict]

    def aliases(option):

        aliasedlist = [
             ["Abzan", "Junk"],
             ["Affinity", "Robots"],
             ["Tron", "RG Tron"],
             ["Suicide Zoo", "Death's Shadow Zoo"],
             ["Abzan Company", "Melira Company", "Abzan CoCo"],
             ["Merfolk", "Fish"],
             ["Jeskai Control", "Nahiri Control", "Jeskai Nahiri"],
             ["Hatebears", "Death and Taxes"]
            ]

        for aliased in aliasedlist:
            if option in aliased:
                return aliased

        # If option has no aliases.
        return []

    return nearestString(query, options=archetypes, transformations=[aliases], method='partial_ratio')


#FINISHED
def nearestCardname(query):

    cardnames = mtgjson.cardnames

    # The name of a legendary card without the epithet.
    def legendname(cardname):
        return cardname.split(',')[0]

    return nearestString(query, options=cardnames, transformations=[legendname], method='ratio')


#print nearestCardname('Litnin Bolt')

#print nearestDeckname("jesk nahiri")