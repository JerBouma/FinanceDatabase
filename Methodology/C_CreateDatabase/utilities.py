import pickle
import json


def read_pickle(pickle_file):
    data_file = pickle.load(open(pickle_file, 'rb'))
    return data_file


def dump_pickle(data, pickle_file):
    pickle.dump(data, open(pickle_file, 'wb'))


def read_json(json_file):
    data_file = json.load(open(json_file, 'rb'))
    return data_file


def sort_dictionary(dictionary):
    sorted_names = sorted(dictionary.keys(), key=str.lower)

    sorted_dictionary = {}
    for symbol in sorted_names:
        sorted_dictionary[symbol] = dictionary[symbol]

    return sorted_dictionary


def fix_broken_pickles(file, new_name, return_data=False):
    pickle.Unpickler = pickle._Unpickler
    import dill

    obj = open(file, 'rb')
    unpickler = dill.Unpickler(obj)

    try:
        unpickler.load()
    except EOFError:
        pass

    data = unpickler.memo[0]

    with open(new_name, 'wb') as handle:
        pickle.dump(data, handle)

    if return_data:
        return data
