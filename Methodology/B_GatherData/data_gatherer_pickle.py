import pickle
from colorama import Fore
from yfinance.utils import get_json
import os
import multiprocessing as mp
from tqdm import tqdm
import time

REMOVE_ALL_EMPTY_PICKLES = True
SKIP_LIST = ['Futures', 'Option']

# Load the generic pickle and create a ticker list
PICKLE_NAME_OF_ALL_SYMBOLS = "generic.pickle"
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
my_file = os.path.join(THIS_FOLDER, PICKLE_NAME_OF_ALL_SYMBOLS)
ticker_list = pickle.load(open(my_file, "rb")).symbols


def initialize():
    # Create a data folder in case it does not exist yet
    if 'Data' not in os.listdir():
        os.mkdir('Documents/Finance Database Dataset/Data')
    else:
        # Determine whether pickles are corrupted. If so remove them so they are added again
        # in the next section
        if REMOVE_ALL_EMPTY_PICKLES:
            print("Checking for corrupted pickles and removing empty pickles..")
        else:
            print("Checking for corrupted pickles..")
        options = os.listdir('Documents/Finance Database Dataset/Data')

        if "Blacklist.pickle" in options:
            options.remove("Blacklist.pickle")
        if 'Blacklist.pickle' not in os.listdir('Documents/Finance Database Dataset/Data'):
            Blacklist = {}
            for option in options:
                Blacklist[option] = {}
            with open(f"Documents/Finance Database Dataset/Data/Blacklist.pickle", 'wb') as handle:
                pickle.dump(Blacklist, handle, protocol=pickle.HIGHEST_PROTOCOL)

        Blacklist = pickle.load(open("Documents/Finance Database Dataset/Data/Blacklist.pickle", "rb"))
    
        for option in tqdm(options):
            if option in SKIP_LIST:
                continue
            tickers = [s.strip('.pickle') for s in os.listdir(f"Data/{option}")]
            for ticker in tickers:
                try:
                    pickle_data = pickle.load(open(f"Data/{option}/{ticker}.pickle", "rb"))
                    if REMOVE_ALL_EMPTY_PICKLES and not pickle_data and option not in SKIP_LIST:
                        if ticker not in Blacklist[option]:
                            Blacklist[option][ticker] = 1
                        elif Blacklist[option][ticker] == 3:
                            print(f"{Fore.LIGHTRED_EX} Data for {ticker} ({option}) is fully Blacklisted "
                                  f"thus not removing")
                            continue
                        elif Blacklist[option][ticker] < 3:
                            print(f"{Fore.RED} Data for {ticker} ({option}) is empty thus removing as "
                                  f"REMOVE_ALL_EMPTY_PICKLES is {REMOVE_ALL_EMPTY_PICKLES} "
                                  f"and Blacklist number {Blacklist[option][ticker]} < 3")
                        Blacklist[option][ticker] = Blacklist[option][ticker] + 1
                        os.remove(f"Data/{option}/{ticker}.pickle")
                except Exception as error:
                    print(f"{Fore.RED} Could not read (and thus removing) {ticker} due to: {error}")
                    os.remove(f"Data/{option}/{ticker}.pickle")
        with open(f"Documents/Finance Database Dataset/Data/Blacklist.pickle", 'wb') as handle:
            pickle.dump(Blacklist, handle, protocol=pickle.HIGHEST_PROTOCOL)


def collect_data(ticker):
    url = "https://finance.yahoo.com/quote/" + ticker
    try:
        retry_times = [5, 10, 20, 30, 40, 50, 60]
        retries = 0
        symbol_type = ticker_list[ticker].symbolTypeDisplay
        ticker = ticker.replace('*', '').replace('\\', '')

        if symbol_type not in os.listdir('Documents/Finance Database Dataset/Data'):
            os.mkdir(f'Data/{symbol_type}')
        if symbol_type in SKIP_LIST:
            with open(f"Data/{symbol_type}/{ticker}.pickle", 'wb') as handle:
                pickle.dump({}, handle, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"{Fore.RED} Empty pickle saved for {ticker} due to it being a {symbol_type}.\n")
        if f"{ticker}.pickle" in os.listdir(f"Data/{symbol_type}"):
            print(f"{Fore.GREEN} {ticker} ({symbol_type}) already collected. \n")
            return None
        while not get_json("https://finance.yahoo.com/quote/AAPL"):
            print(f"{Fore.RED} Waiting {retry_times[retries]} seconds..")
            time.sleep(retry_times[retries])
            if retry_times[retries] != 60:
                retries += 1
        data = get_json(url)
    except Exception as error:
        print(f"{Fore.RED} Not able to find the data for {ticker} by checking the url {url} due to {error}. \n")
        return None
    try:
        with open(f"Data/{symbol_type}/{ticker}.pickle", 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"{Fore.BLUE} {ticker} downloaded and stored in {symbol_type}. \n")
    except Exception as error:
        print(f"{Fore.RED} Was not able to write to pickle due to: {error}. \n")


def collect_data_issue_8(ticker):
    url = "https://finance.yahoo.com/quote/" + ticker
    symbol_type = 'Equity'
    try:
        retry_times = [5, 10, 20, 30, 40, 50, 60]
        retries = 0
        ticker = ticker.replace('*', '').replace('\\', '')

        if f"{ticker}.pickle" in os.listdir(f"Data/{symbol_type}"):
            print(f"{Fore.GREEN} {ticker} ({symbol_type}) already collected. \n")
            return None
        while not get_json("https://finance.yahoo.com/quote/AAPL"):
            print(f"{Fore.RED} Waiting {retry_times[retries]} seconds..")
            time.sleep(retry_times[retries])
            if retry_times[retries] != 60:
                retries += 1
        data = get_json(url)
    except Exception as error:
        print(f"{Fore.RED} Not able to find the data for {ticker} by checking the url {url} due to {error}. \n")
        return None

    try:
        with open(f"Data/{symbol_type}/{ticker}.pickle", 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"{Fore.BLUE} {ticker} downloaded and stored in {symbol_type}. \n")
    except Exception as error:
        print(f"{Fore.RED} Was not able to write to pickle due to: {error}. \n")


def collect_data_based_on_txt_for_issue_8():
    pool = mp.Pool(mp.cpu_count())
    print(f"{Fore.LIGHTYELLOW_EX} Starting CPUs..")
    result = pool.map(collect_data_issue_8, ticker_symbols_issue_8)
    print(f"{Fore.LIGHTYELLOW_EX} Ready!")


def collect_data_based_on_pickle():
    pool = mp.Pool(mp.cpu_count())
    print(f"{Fore.LIGHTYELLOW_EX} Starting CPUs..")
    result = pool.map(collect_data, ticker_symbols)
    print(f"{Fore.LIGHTYELLOW_EX} Ready!")


if __name__ == "__main__":
    print(f"{Fore.YELLOW} Initalizing..")
    initialize()

    print(f"{Fore.YELLOW} Loading tickers....")
    ticker_symbols = list(ticker_list.keys())
    ticker_symbols_issue_8 = open("Documents/Finance Database Dataset/Issues/Issues - 8.txt", "r").read().split("\n")

    # Determine which pickles are already created so they are not included in the total list
    already_collected = []
    options = os.listdir('Documents/Finance Database Dataset/Data')
    if "Blacklist.pickle" in options:
        options.remove("Blacklist.pickle")

    for folder in options:
        already_collected.extend([s.strip('.pickle') for s in os.listdir(f"Data/{folder}")])
    already_collected_issue_8 = []
    for item in ticker_symbols_issue_8:
        if item in already_collected:
            already_collected_issue_8.extend([item])

    # Remove already collected tickers from the total list
    ticker_symbols = list(set(ticker_symbols) - set(already_collected) - set(already_collected_issue_8))
    ticker_symbols_issue_8 = list(set(ticker_symbols_issue_8) - set(already_collected_issue_8))

    if ticker_symbols:
        print(f"{Fore.YELLOW} Starting General Data collection")
        collect_data_based_on_pickle()
    if ticker_symbols_issue_8:
        print(f"{Fore.YELLOW} Starting Data collection for Issue 8")
        collect_data_based_on_txt_for_issue_8()  # See: https://github.com/JerBouma/FinanceDatabase/issues/8
