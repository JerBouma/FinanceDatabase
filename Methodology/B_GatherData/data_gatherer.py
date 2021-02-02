import pickle
from tqdm import tqdm
from yfinance.utils import get_json
import os

PICKLE_NAME_OF_ALL_SYMBOLS = 'generic.pickle'

# Load pickle with data
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
my_file = os.path.join(THIS_FOLDER, PICKLE_NAME_OF_ALL_SYMBOLS)
ticker_list = pickle.load(open(my_file, "rb")).symbols

try:
    DoneList = pickle.load(open("DoneList.pickle", "rb"))
    Equities = pickle.load(open("Equities.pickle", "rb"))
    ETFs = pickle.load(open("ETFs.pickle", "rb"))
    Funds = pickle.load(open("Funds.pickle", "rb"))
    Indices = pickle.load(open("Indices.pickle", "rb"))
    Currencies = pickle.load(open("Currencies.pickle", "rb"))
    Futures = pickle.load(open("Futures.pickle", "rb"))
    CryptoCurrencies = pickle.load(open("CryptoCurrencies.pickle", "rb"))
    MoneyMarkets = pickle.load(open("MoneyMarkets.pickle", "rb"))
    Options = pickle.load(open("Options.pickle", "rb"))
    Errors = pickle.load(open("Errors.pickle", "rb"))
except Exception as e:
    print("Not all dictionaries and/or the list of done tickers is created.")
    print("Error: " + str(e))
    check = input("Do you want to start fresh? (yes/no):")
    if check == 'yes':
        Equities = {}
        ETFs = {}
        Funds = {}
        Indices = {}
        Currencies = {}
        Futures = {}
        CryptoCurrencies = {}
        MoneyMarkets = {}
        Options = {}
        Errors = {}
        DoneList = []
    else:
        print("You typed {INPUT} which isn't 'yes' thus stopping program.".format(INPUT=check))
        raise ValueError("Program was stopped.")


def save_to_pickle():
    with open('Equities.pickle', 'wb') as handle:
        pickle.dump(Equities, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('ETFs.pickle', 'wb') as handle:
        pickle.dump(ETFs, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Funds.pickle', 'wb') as handle:
        pickle.dump(Funds, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Indices.pickle', 'wb') as handle:
        pickle.dump(Indices, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Currencies.pickle', 'wb') as handle:
        pickle.dump(Currencies, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Futures.pickle', 'wb') as handle:
        pickle.dump(Futures, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('CryptoCurrencies.pickle', 'wb') as handle:
        pickle.dump(CryptoCurrencies, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('MoneyMarkets.pickle', 'wb') as handle:
        pickle.dump(MoneyMarkets, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Options.pickle', 'wb') as handle:
        pickle.dump(Options, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('Errors.pickle', 'wb') as handle:
        pickle.dump(Errors, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('DoneList.pickle', 'wb') as handle:
        pickle.dump(DoneList, handle, protocol=pickle.HIGHEST_PROTOCOL)


# Start counter for saving to pickle and make TemporaryList
counter_for_saving = 0
TemporaryList = []

for ticker in tqdm(ticker_list):
    # When already done, continue
    if ticker in DoneList:
        continue

    # Add to temporary list
    TemporaryList.append(ticker)

    # Save everything perodically
    if counter_for_saving == 100:
        counter_for_saving = 0
        for ticker in TemporaryList:
            DoneList.append(ticker)
        TemporaryList = []
        save_to_pickle()

    # Increase counter by 1
    counter_for_saving += 1

    try:
        data = get_json("https://finance.yahoo.com/quote/" + ticker)
        symbol_type = ticker_list[ticker].symbolTypeDisplay
    except Exception as e:
        print("Not able to find the data for {TICKER} by checking the url {URL} due to {ERROR}.".format(
            TICKER=ticker, URL="https://finance.yahoo.com/quote/" + ticker, ERROR=e))
        Errors[ticker] = "Not able to find the data for {TICKER} by checking the url {URL} due to {ERROR}.".format(
            TICKER=ticker, URL="https://finance.yahoo.com/quote/" + ticker, ERROR=e)
        continue

    try:
        if symbol_type == 'Equity':
            Equities[ticker] = data
        elif symbol_type == "ETF":
            ETFs[ticker] = data
        elif symbol_type == "Fund":
            Funds[ticker] = data
        elif symbol_type == "Index":
            Indices[ticker] = data
        elif symbol_type == "Currency":
            Currencies[ticker] = data
        elif symbol_type == "Futures":
            Futures[ticker] = data
        elif symbol_type == 'CRYPTOCURRENCY':
            CryptoCurrencies[ticker] = data
        elif symbol_type == 'MoneyMarket':
            MoneyMarkets[ticker] = data
        elif symbol_type == 'Option':
            Options[ticker] = data
        else:
            print("The symbol type ({TYPE}) of {TICKER} is not an option".format(
                TICKER=symbol_type, TYPE=ticker))
            Errors[ticker] = "The symbol type ({TYPE}) of {TICKER} is not an option.".format(
                TYPE=symbol_type, TICKER=ticker)
            continue
    except Exception:
        print("Not able to find the data for {TICKER} with type {TYPE}.".format(
            TICKER=ticker, TYPE=symbol_type))
        Errors[ticker] = "Not able to find the data for {TICKER} with type {TYPE}.".format(
            TICKER=ticker, TYPE=symbol_type)
        continue

# Final Save
save_to_pickle()
