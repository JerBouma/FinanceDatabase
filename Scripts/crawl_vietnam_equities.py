import os
import requests
import json
import numpy as np
import shutil

"""
curl 'https://fiin-fundamental.ssi.com.vn/Snapshot/GetSnapshotNoneBank?language=vi&OrganCode=SSI' \
>   -H 'authority: fiin-fundamental.ssi.com.vn' \
>   -H 'accept: application/json' \
>   -H 'accept-language: en-US,en;q=0.9' \
>   -H 'content-type: application/json' \
>   -H 'origin: https://iboard.ssi.com.vn' \
>   -H 'referer: https://iboard.ssi.com.vn/' \
>   -H 'sec-ch-ua: "Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"' \
>   -H 'sec-ch-ua-mobile: ?0' \
>   -H 'sec-ch-ua-platform: "Linux"' \
>   -H 'sec-fetch-dest: empty' \
>   -H 'sec-fetch-mode: cors' \
>   -H 'sec-fetch-site: same-site' \
>   -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36' \
>   -H 'x-fiin-key: KEY' \
>   -H 'x-fiin-seed: SEED' \
>   -H 'x-fiin-user-id: ID' \
>   --compressed

"""

def get_organ_code(organ_data, symbol):
    organ_data = organ_data["items"]
    for item in organ_data:
        if symbol == item["ticker"]:
            return item["organCode"]


def get_symbol_snapshot(symbol, use_cache=True):
    cache_dir = ".cache/snapshot"
    organ_path = ".cache/organization.json"

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    cache_file = os.path.join(cache_dir, symbol + ".json")
    if use_cache:
        if os.path.exists(cache_file):
            return json.load(open(cache_file))["items"][0]["summary"]
        
    headers = {
        'authority': 'fiin-fundamental.ssi.com.vn',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'content-type': 'application/json',
        'x-fiin-key': 'KEY',
        'x-fiin-seed': 'SEED',
        'x-fiin-user-id': 'ID'
    }
    list_organ_url = f"https://fiin-core.ssi.com.vn/Master/GetListOrganization?language=vi"
    if use_cache and os.path.exists(organ_path):
        organ_data = json.load(open(organ_path))
    else:
        organ_data = requests.get(list_organ_url, headers=headers).json()
        with open(organ_path, "w") as fobj:
            json.dump(organ_data, fobj)
    organ_code = get_organ_code(organ_data, symbol)
    print(f"INFO: Get snapshot for code {symbol}, organCode {organ_code}")
    url = f"https://fiin-fundamental.ssi.com.vn/Snapshot/GetSnapshotNoneBank?language=vi&OrganCode={organ_code}"

    data = requests.get(url, headers=headers).json()

    with open(cache_file, "w") as fobj:
        json.dump(data, fobj)
    
    return data["items"][0]["summary"]


def get_companies_mc(equities):
    results = {}
    for code, v in equities.items():
        if v.get("type") == "STOCK":
            snapshot = get_symbol_snapshot(code)
            if snapshot is None:
                continue
            mc = snapshot["rtd11"]
            if mc is None:
                continue
            results[code] = mc
    return results


def get_company_size(companies_mc, symbol):
    if symbol not in companies_mc:
        return None

    if companies_mc[symbol] > 24*1e12:
        return "Large Cap"
    
    if companies_mc[symbol] > 2*1e12:
        return "Mid Cap"

    if companies_mc[symbol] > 5e10:
        return "Small Cap"

    if companies_mc[symbol] > 2e10:
        return "Micro Cap"
    
    return "Nano Cap"


def normalize_name(name):
    name = name.lower()
    tokens = [x[0].upper()+x[1:] for x in name.split()]
    
    return " ".join(tokens)


def export_equities(
    equities, 
    symbol_to_sectors, 
    symbol_to_industries,
    sectors, industries, 
    sectors_by_industries):
    companies_mc = get_companies_mc(equities)
    results = {}
    for code, v in equities.items():
        if v.get("type") == "STOCK":
            sector_name = None
            ind_id = symbol_to_industries[code]
            if code not in symbol_to_sectors:
                
                sector_id = sectors_by_industries[ind_id]
                sector_name = sectors[sector_id]["vietnameseName"]
            else:
                sector_id = symbol_to_sectors[code]
                sector_name = sectors[sector_id]["vietnameseName"]

            item = {
                "short_name": v.get("shortName", v.get("companyName")),
                "long_name": v["companyName"],
                "summary": None,
                "currency": "VND",
                "sector": sector_name,
                "industry": industries[ind_id]["vietnameseName"],
                "exchange": v["floor"],
                "market": "vn_market",
                "country": "vietnam",
                "state": None,
                "city": None,
                "zipcode": None,
                "website": None,
                "market_cap": get_company_size(companies_mc, code)
            }
            results[code] = item
    return results


def crawl_equities(output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    url = "https://api-finfo.vndirect.com.vn/v4/industry_classification?q=industryLevel:1&size=100"
    ind_lv1 = requests.get(url, headers=headers).json()
    
    url = "https://api-finfo.vndirect.com.vn/v4/industry_classification?q=industryLevel:2&size=100"
    ind_lv2 = requests.get(url, headers=headers).json()

    url = "https://api-finfo.vndirect.com.vn/v4/industry_classification?q=industryLevel:3&size=100"
    ind_lv3 = requests.get(url, headers=headers).json()

    url = "https://api-finfo.vndirect.com.vn/v4/industry_classification?q=industryLevel:4&size=100"
    ind_lv4 = requests.get(url, headers=headers).json()

    # Industries by code
    ind_dict = {}

    for d in [ind_lv1, ind_lv2, ind_lv3, ind_lv4]:
        for item in d["data"]:
            ind_dict[item["industryCode"]] = item

    sectors = {}
    industries = {}
    ind_lvl = {}

    symbol_to_sectors = {}
    symbol_to_industries = {}

    for k, v in ind_dict.items():
        v["englishName"] = normalize_name(v["englishName"])
        v["vietnameseName"] = normalize_name(v["vietnameseName"])

        if v["industryLevel"] == "1":
            sectors[k] = v
            for code in v["codeList"].split(","):
                symbol_to_sectors[code] = k
        if v["industryLevel"] == "4":
            industries[k] = v
            for code in v["codeList"].split(","):
                symbol_to_industries[code] = k
        if v["industryLevel"] != "1":
            ind_lvl[k] = v["higherLevelCode"]

    sectors_by_industries = {}

    for k, v in industries.items():
        parent = ind_dict[ind_lvl[k]]
        while parent.get("higherLevelCode") is None:
            parent = ind_dict[ind_lvl[parent["industryCode"]]]
        sectors_by_industries[k] = parent["industryCode"]
        
    equities = {}
    url = "https://api-finfo.vndirect.com.vn/v4/stocks?q=type:IFC,ETF,STOCK~status:LISTED&fields=code,type,companyName,companyNameEng,shortName,floor,industryName&size=10000"
    data = requests.get(url, headers=headers).json()["data"]

    for item in data:
       equities[item["code"]] = item

    norm_equities = export_equities(
        equities, 
        symbol_to_sectors, 
        symbol_to_industries, 
        sectors, industries,
        sectors_by_industries)

    sectors_n = {}
    industries_n = {}
    for k, v in norm_equities.items():
        if v["sector"] not in sectors_n:
            sectors_n[v["sector"]] = []
        sectors_n[v["sector"]].append({k: v})

        if v["industry"] not in industries_n:
            industries_n[v["industry"]] = []
        industries_n[v["industry"]].append({k: v})

    print(f"INFO: Dump sectors")
    with open(os.path.join(output_dir, "Vietnam Sectors.json"), "w") as fobj:
        json.dump(sorted(list(sectors_n.keys())), fobj, indent=2)

    print(f"INFO: Dump industries")
    with open(os.path.join(output_dir, "Vietnam Industries.json"), "w") as fobj:
        json.dump(sorted(industries_n.keys()), fobj, indent=2)

    industries_dir = os.path.join(output_dir, "Industries")
    os.makedirs(industries_dir , exist_ok=True)

    for k, v in sectors_n.items():
        sector_dir = os.path.join(output_dir, k)
        os.makedirs(sector_dir, exist_ok=True)
        industries_by_sector = set()
        for e in v:
            industries_by_sector.add(e[list(e.keys())[0]]["industry"])
        ibs_file = os.path.join(sector_dir, f"_{k} Industries.json")
        all_e_file = os.path.join(sector_dir, f"_{k}.json")

        with open(ibs_file, "w") as fobj:
            json.dump(sorted(list(industries_by_sector)), fobj, indent=2)

        z = sorted(v, key=lambda x: x[list(x.keys())[0]]["long_name"])
        with open(all_e_file, "w") as fobj:
            json.dump(z, fobj, indent=2)

        for id in industries_by_sector:
            idf = os.path.join(sector_dir, f"{id}.json")
            idf_copy = os.path.join(industries_dir, f"{id}.json")
            with open(idf, "w") as fobj:
                json.dump(industries_n[id], fobj, indent=2)
            shutil.copyfile(idf, idf_copy)
            

    # print(f"INFO: Dump equities by sectors")
    # for k, v in norm_equities.items():
    #     print(k, v)
    with open(os.path.join(output_dir, "Vietnam.json"), "w") as fobj:
        json.dump(norm_equities, fobj, indent=2)



if __name__ == "__main__":
    crawl_equities("Database/Equities/Countries/Vietnam")
