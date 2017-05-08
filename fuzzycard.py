# -*- coding: utf-8 -*-

# Import standard modules.
from fuzzywuzzy import fuzz


class ApproximateString(object):
    def __init__(self, target, options):
        self.string = target
        self.options = options

    def nearest_object(self):
        return max(self.options)

    def nearest(self):
        return unicode(self.nearest_object())

    def __str__(self):
        return self.nearest()

    __repr__ = __str__


class ProspectiveString(object):
    def __init__(self, target, prospect, transformations=(), untransformed=None):
        self.target = target
        self.prospect = prospect
        self.transformations = transformations
        self.untransformed = untransformed

    def score(self):
        return fuzz.ratio(self.target, self.prospect)

    def bestscore(self):
        return max(transformed.score() for transformed in self.transform())

    def transform(self):
        transformed = [self]
        for f in self.transformations:
            next_transformed = getattr(self, f)()
            if isinstance(next_transformed, list):
                transformed += next_transformed
            else:
                transformed.append(next_transformed)
        return transformed

    def get_string(self):
        return self.untransformed.prospect if self.untransformed else self.prospect

    def __eq__(self, other):
        return self.bestscore() == other.bestscore()

    def __lt__(self, other):
        return self.bestscore() < other.bestscore()

    def __str__(self):
        return self.prospect


class ApproximateDeckname(ApproximateString):
    def __init__(self, bot, target, format_=None):
        self.bot = bot
        self.master = bot.metagame.content
        self.target = target
        self.format_ = format_
        self.options = self.get_options()
        ApproximateString.__init__(self, target=self.target, options=self.options)

    def get_options(self):
        namedict = self.master.decknames(formatname=self.format_, show_formats=True)
        return [ProspectiveDeckname(target=self.target, prospect=archetype, format_=namedict[archetype])
                for archetype in namedict]

    def nearest_format(self):
        return self.nearest_object().format_


class ProspectiveDeckname(ProspectiveString):
    def __init__(self, target, prospect, format_, untransformed=None):
        self.target = target
        self.prospect = prospect
        self.format_ = format_
        self.untransformed = untransformed
        self.transformations = ["_aliased"]
        ProspectiveString.__init__(self, target=self.target, prospect=self.prospect, transformations=self.transformations)

    def _aliased(self):
        alias_sets = [
            ["Abzan", "Junk"],
            ["Affinity", "Robots"],
            ["Tron", "RG Tron"],
            ["Suicide Zoo", "Death's Shadow Zoo", "Zooicide"],
            ["Abzan Company", "Melira Company", "Abzan CoCo"],
            ["Merfolk", "Fish"],
            ["Jeskai Control", "Nahiri Control", "Jeskai Nahiri"],
            ["Hatebears", "Death and Taxes"]
        ]
        for alias_set in alias_sets:
            if self.prospect in alias_set:
                return [ProspectiveDeckname(target=self.target, prospect=deckname, format_=self.format_, untransformed=self)
                        for deckname in alias_set]
        return []


class ApproximateCardname(ApproximateString):
    def __init__(self, bot, target):
        self.bot = bot
        self.target = target
        self.options = self.get_options()
        ApproximateString.__init__(self, target=self.target, options=self.options)

    def get_options(self):
        return [ProspectiveCardname(target=self.target, prospect=cardname) for cardname in self.bot.carddata.content.cardnames]


class ProspectiveCardname(ProspectiveString):
    def __init__(self, target, prospect, untransformed=None):
        self.target = target
        self.prospect = prospect
        self.untransformed = untransformed
        self.transformations = ["_noepithet"]
        ProspectiveString.__init__(self, target=self.target, prospect=self.prospect, transformations=self.transformations)

    def _noepithet(self):
        if ',' in self.prospect:
            epithetless = self.prospect.split(',', 1)[0]
            return ProspectiveCardname(target=self.target, prospect=epithetless, untransformed=self)
        else:
            return []


if __name__ == "__main__":
    print ApproximateCardname(target="lightnng bolt")
    print ApproximateCardname(target="ligni btot")
    print ApproximateCardname(target="rago")
    print ApproximateCardname(target="tramgoyf")

    print ApproximateDeckname(target="junk", format_="Modern")
    print ApproximateDeckname(target="mricls")

    print ApproximateDeckname(target='affinity', format_=None)