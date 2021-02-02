from .compat import is_py3, text

class Symbol:
    """Abstract class"""
    def __init__(self, ticker, name, exchange):
        self.ticker = ticker
        self.name = name # <--- may be "None"
        self.exchange = exchange # <--- may be "None" too for some reason

    def getType(self):
        return "Undefined"

    def getRow(self):
        return [self.ticker, self.name, self.exchange]

    def __unicode__(self):
        return u"" + self.getType() + " " + self.ticker + " " + text(self.exchange) + " " + text(self.name)

if is_py3:
    Symbol.__str__ = Symbol.__unicode__

