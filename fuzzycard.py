# Import standard modules.
from collections import namedtuple
from fuzzywuzzy import fuzz
# Import custom modules.
import metagame
import mtgjson


class ApproximateString(object):
    def __init__(self, target, options):
        self.string = target
        self.options = options

    def nearestobject(self):
        return max(self.options)

    def nearest(self):
        return unicode(self.nearestobject())

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
        for function in self.transformations:
            nexttransformed = getattr(self, function)()
            if isinstance(nexttransformed, list):
                transformed += nexttransformed
            else:
                transformed.append(nexttransformed)
        return transformed

    def getString(self):
        return self.untransformed.prospect if self.untransformed else self.prospect

    def __eq__(self, other):
        return self.bestscore() == other.bestscore()

    def __lt__(self, other):
        return self.bestscore() < other.bestscore()

    def __str__(self):
        return self.prospect


class ApproximateDeckname(ApproximateString):
    def __init__(self, target, format_=None):
        self.master = metagame.load_metagamemaster("metagamemaster.p")
        self.target = target
        self.format_ = format_
        self.options = self.getOptions()
        ApproximateString.__init__(self, target=self.target, options=self.options)

    def getOptions(self):
        if self.format_:
            return [ProspectiveDeckname(target=self.target, prospect=archetype.archetype, format_=archetype.format_)
                    for archetype in self.master[self.format_].archetypes()]
        else:
            return [ProspectiveDeckname(target=self.target, prospect=archetype.archetype, format_=archetype.format_)
                    for archetype in self.master.archetypes()]

    def nearestformat(self):
        return self.nearestobject().format_


class ProspectiveDeckname(ProspectiveString):
    def __init__(self, target, prospect, format_, untransformed=None):
        self.target = target
        self.prospect = prospect
        self.format_ = format_
        self.untransformed = untransformed
        self.transformations = ["_aliased"]
        ProspectiveString.__init__(self, target=self.target, prospect=self.prospect, transformations=self.transformations)

    def _aliased(self):
        aliassets = [
            ["Abzan", "Junk"],
            ["Affinity", "Robots"],
            ["Tron", "RG Tron"],
            ["Suicide Zoo", "Death's Shadow Zoo", "Zooicide"],
            ["Abzan Company", "Melira Company", "Abzan CoCo"],
            ["Merfolk", "Fish"],
            ["Jeskai Control", "Nahiri Control", "Jeskai Nahiri"],
            ["Hatebears", "Death and Taxes"]
        ]
        for aliasset in aliassets:
            if self.prospect in aliasset:
                return [ProspectiveDeckname(target=self.target, prospect=deckname, format_=self.format_, untransformed=self)
                        for deckname in aliasset]
        return []



class ApproximateCardname(ApproximateString):
    def __init__(self, target):
        self.target = target
        self.options = self.getOptions()
        ApproximateString.__init__(self, target=self.target, options=self.options)

    def getOptions(self):
        return [ProspectiveCardname(target=self.target, prospect=cardname) for cardname in mtgjson.cardnames]


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
    print ApproximateCardname("lightnng bolt")
    print ApproximateCardname("ligni btot")
    print ApproximateCardname("rago")
    print ApproximateCardname("tramgoyf")

    print ApproximateDeckname("junk", "Modern")
    print ApproximateDeckname("mricls")

    print ApproximateDeckname('affinity', None)