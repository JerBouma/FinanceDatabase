import degiroapi
from core_selection_degiro_isin import isin
from yfinance.utils import get_json
from utilities import dump_pickle, read_json, sort_dictionary
from etfs_creator import fill_data_points_etfs
import json
from tqdm import tqdm
import os


def get_core_selection_data(username, password):
    degiro = degiroapi.DeGiro()
    degiro.login(username, password)

    data_set = {}
    print("Prepare dictionary..")
    for symbol in tqdm(isin):
        try:
            searcher = degiro.search_products(symbol)
            data_set[f"{searcher[0]['symbol']}.{isin[symbol]}"] = {}
            data_set[f"{searcher[0]['symbol']}.{isin[symbol]}"]['name'] = searcher[0]['name']
            data_set[f"{searcher[0]['symbol']}.{isin[symbol]}"]['ISIN'] = symbol
        except Exception as e:
            print(f"Error for {symbol} dictionary preparing: {e}")

    data_set_with_data = {}
    print("Collecting data..")
    for symbol in tqdm(data_set):
        try:
            data_set_with_data[symbol] = get_json("https://finance.yahoo.com/quote/" + symbol)
            data_set_with_data[symbol]['ISIN'] = data_set[symbol]['ISIN']
        except Exception as e:
            print(f"Error for {symbol} data collection: {e}")

    dump_pickle(data_set_with_data, 'core_selection_degiro.pickle')

    return data_set_with_data


def collect_core_selection_data(username, password, use_json=False):
    data_set = get_core_selection_data(username, password)

    try:
        os.mkdir("DeGiro")
    except Exception:
        print("DeGiro folder already exists")

    if use_json:
        data_set_filled = read_json(r"DeGiro/core_selection_filled.json")
    else:
        print("Filling JSON data_set_filled..")
        data_set_filled = {}
        for symbol in tqdm(data_set):
            data_set_filled[symbol] = fill_data_points_etfs(data_set[symbol])
            data_set_filled[symbol]['ISIN'] = data_set[symbol]['ISIN']

        with open(r"DeGiro/core_selection_filled.json", 'w') as handle:
            sorted_data_set_filled = sort_dictionary(data_set_filled)
            json.dump(sorted_data_set_filled, handle, indent=4)

    # Make legit data set
    print("Filling JSON data_set_filtered..")
    data_set_filtered = {}
    for symbol in data_set_filled:
        if data_set_filled[symbol]['summary'] is not None:
            data_set_filtered[symbol] = data_set_filled[symbol]
            data_set_filtered[symbol]['ISIN'] = data_set[symbol]['ISIN']

    with open(r"DeGiro/core_selection_filtered.json", 'w') as handle:
        sorted_data_set_filtered = sort_dictionary(data_set_filtered)
        json.dump(sorted_data_set_filtered, handle, indent=4)
    print("Done!")

    return data_set_filtered
