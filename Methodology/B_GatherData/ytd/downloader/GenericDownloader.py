from ..SimpleSymbolDownloader import SymbolDownloader
from ..symbols.Generic import Generic

from ..compat import text

class GenericDownloader(SymbolDownloader):
    def __init__(self):
        SymbolDownloader.__init__(self, "generic")

    def decodeSymbolsContainer(self, json):
        symbols = []
        count = 0

        for row in json['data']['items']:
            ticker = text(row['symbol'])
            name = row['name']
            exchange = row['exch']
            exchangeDisplay = row['exchDisp']
            symbolType = row['type']
            symbolTypeDisplay = row['typeDisp']
            symbols.append(Generic(ticker, name, exchange, exchangeDisplay, symbolType, symbolTypeDisplay))

        count = len(json['data']['items'])

        return (symbols, count)

    def getRowHeader(self):
        return SymbolDownloader.getRowHeader(self) + ["exchangeDisplay", "Type", "TypeDisplay"]

