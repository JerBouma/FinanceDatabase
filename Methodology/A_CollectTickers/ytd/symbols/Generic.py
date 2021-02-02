from ytd.Symbol import Symbol

class Generic(Symbol):
    def __init__(self, ticker, name, exchange, exchangeDisplay, symbolType, symbolTypeDisplay):
        Symbol.__init__(self, ticker, name, exchange)
        self.exchangeDisplay = exchangeDisplay
        self.symbolType = symbolType
        self.symbolTypeDisplay = symbolTypeDisplay

    def getType(self):
        return 'Generic'

    def getRow(self):
        return Symbol.getRow(self) + [self.exchangeDisplay, self.symbolType, self.symbolTypeDisplay]
