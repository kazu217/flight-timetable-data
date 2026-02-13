#!/usr/bin/env python3
"""Scrape domestic flight timetable data from ekitan.com"""

import urllib.request
import re
import json
import time
import sys
import os

# Ekitan airport ID → (IATA code, short name, full name, region)
EKITAN_AIRPORTS = {
    1:  ("WKJ", "稚内", "稚内空港", "北海道"),
    2:  ("MBE", "紋別", "紋別空港", "北海道"),
    3:  ("MMB", "女満別", "女満別空港", "北海道"),
    4:  ("CTS", "新千歳", "新千歳空港", "北海道"),
    5:  ("AKJ", "旭川", "旭川空港", "北海道"),
    6:  ("SHB", "中標津", "中標津空港", "北海道"),
    7:  ("OKD", "丘珠", "札幌丘珠空港", "北海道"),
    8:  ("KUH", "釧路", "釧路空港", "北海道"),
    9:  ("OBO", "帯広", "とかち帯広空港", "北海道"),
    10: ("HKD", "函館", "函館空港", "北海道"),
    59: ("RIS", "利尻", "利尻空港", "北海道"),
    60: ("OIR", "奥尻", "奥尻空港", "北海道"),
    11: ("AOJ", "青森", "青森空港", "東北"),
    12: ("MSJ", "三沢", "三沢空港", "東北"),
    13: ("ONJ", "大館能代", "大館能代空港", "東北"),
    14: ("AXT", "秋田", "秋田空港", "東北"),
    15: ("HNA", "花巻", "いわて花巻空港", "東北"),
    16: ("SYO", "庄内", "庄内空港", "東北"),
    17: ("GAJ", "山形", "おいしい山形空港", "東北"),
    18: ("SDJ", "仙台", "仙台空港", "東北"),
    20: ("FKS", "福島", "福島空港", "東北"),
    21: ("NRT", "成田", "成田国際空港", "関東"),
    22: ("HND", "羽田", "東京国際空港（羽田）", "関東"),
    63: ("HAC", "八丈島", "八丈島空港", "関東"),
    19: ("KIJ", "新潟", "新潟空港", "中部"),
    23: ("TOY", "富山", "富山空港", "中部"),
    24: ("KMQ", "小松", "小松空港", "中部"),
    25: ("NTQ", "能登", "のと里山空港", "中部"),
    26: ("MMJ", "松本", "信州まつもと空港", "中部"),
    58: ("FSZ", "静岡", "静岡空港", "中部"),
    27: ("NKM", "名古屋", "名古屋飛行場（小牧）", "中部"),
    28: ("NGO", "中部", "中部国際空港（セントレア）", "中部"),
    29: ("ITM", "伊丹", "大阪国際空港（伊丹）", "近畿"),
    30: ("KIX", "関西", "関西国際空港", "近畿"),
    56: ("UKB", "神戸", "神戸空港", "近畿"),
    31: ("SHM", "南紀白浜", "南紀白浜空港", "近畿"),
    32: ("TJH", "但馬", "コウノトリ但馬空港", "近畿"),
    33: ("OKJ", "岡山", "岡山桃太郎空港", "中国"),
    34: ("YGJ", "米子", "米子鬼太郎空港", "中国"),
    35: ("TTJ", "鳥取", "鳥取砂丘コナン空港", "中国"),
    36: ("IWJ", "萩石見", "萩・石見空港", "中国"),
    37: ("IZO", "出雲", "出雲縁結び空港", "中国"),
    64: ("OKI", "隠岐", "隠岐空港", "中国"),
    38: ("HIJ", "広島", "広島空港", "中国"),
    92: ("IWK", "岩国", "岩国錦帯橋空港", "中国"),
    40: ("UBJ", "山口宇部", "山口宇部空港", "中国"),
    41: ("TAK", "高松", "高松空港", "四国"),
    42: ("MYJ", "松山", "松山空港", "四国"),
    43: ("TKS", "徳島", "徳島阿波おどり空港", "四国"),
    44: ("KCZ", "高知", "高知龍馬空港", "四国"),
    45: ("FUK", "福岡", "福岡空港", "九州"),
    46: ("KMI", "宮崎", "宮崎ブーゲンビリア空港", "九州"),
    57: ("KKJ", "北九州", "北九州空港", "九州"),
    48: ("HSG", "佐賀", "佐賀空港", "九州"),
    49: ("NGS", "長崎", "長崎空港", "九州"),
    65: ("TSJ", "対馬", "対馬空港", "九州"),
    66: ("IKI", "壱岐", "壱岐空港", "九州"),
    67: ("FUJ", "五島福江", "五島福江空港", "九州"),
    50: ("OIT", "大分", "大分空港", "九州"),
    51: ("KMJ", "熊本", "熊本空港", "九州"),
    68: ("AXJ", "天草", "天草空港", "九州"),
    52: ("KOJ", "鹿児島", "鹿児島空港", "九州"),
    69: ("TNE", "種子島", "種子島空港", "九州"),
    70: ("KUM", "屋久島", "屋久島空港", "九州"),
    71: ("KKX", "喜界", "喜界空港", "九州"),
    72: ("ASJ", "奄美大島", "奄美空港", "九州"),
    73: ("TKN", "徳之島", "徳之島空港", "九州"),
    74: ("OKE", "沖永良部", "沖永良部空港", "九州"),
    75: ("RNJ", "与論", "与論空港", "九州"),
    53: ("OKA", "那覇", "那覇空港", "沖縄"),
    76: ("KTD", "北大東", "北大東空港", "沖縄"),
    77: ("MMD", "南大東", "南大東空港", "沖縄"),
    79: ("UEO", "久米島", "久米島空港", "沖縄"),
    80: ("MMY", "宮古", "宮古空港", "沖縄"),
    93: ("SHI", "下地島", "下地島空港", "沖縄"),
    81: ("TRA", "多良間", "多良間空港", "沖縄"),
    82: ("ISG", "石垣", "南ぬ島石垣空港", "沖縄"),
    83: ("OGN", "与那国", "与那国空港", "沖縄"),
}

# Ekitan airport name → IATA code (for parsing arrival airports)
EKITAN_NAME_TO_IATA = {}
for eid, (iata, name, fullname, region) in EKITAN_AIRPORTS.items():
    EKITAN_NAME_TO_IATA[name] = iata

# Add ekitan-specific name variants
EKITAN_NAME_TO_IATA.update({
    "新石垣": "ISG",
    "根室中標津": "SHB",
    "関西国際": "KIX",
    "中部国際": "NGO",
    "奄美": "ASJ",
    "萩・石見": "IWJ",
    "札幌丘珠": "OKD",
    "但馬": "TJH",
    "小牧": "NKM",
    "名古屋小牧": "NKM",
    "松本": "MMJ",
})

# Airlines to include
INCLUDE_AIRLINES = {"JAL", "ANA", "ADO", "SNA", "SFJ", "ORC", "IBX", "JTA", "JAC", "HAC", "AMX"}

# Regex pattern for parsing flight entries
FLIGHT_PATTERN = re.compile(
    r'company-data-(\w+)\s+hour-data.*?'
    r'class="dep-time">([\d:]+)<span class="dep-arr-airpot">(.*?)</span>.*?'
    r'class="arr-time">([\d:]+)<span class="dep-arr-airpot">(.*?)</span>.*?'
    r'class="td-required-time">(.*?)</td>',
    re.DOTALL
)

def is_relevant_flight(flight_num):
    """Check if flight should be included"""
    prefix = re.match(r"[A-Z]+", flight_num)
    if not prefix:
        return False
    airline = prefix.group()
    if airline not in INCLUDE_AIRLINES:
        return False
    # Skip ANA codeshares: ANA2xxx(SNA), ANA3xxx(SFJ), ANA4xxx(ADO)
    # Keep ANA1-1999 (genuine ANA flights including regional)
    if airline == "ANA":
        num_str = flight_num[3:]
        if num_str.isdigit():
            num = int(num_str)
            if num >= 2000:
                return False
    return True

def get_airline_from_flight(flight_num):
    """Extract airline code from flight number"""
    m = re.match(r"[A-Z]+", flight_num)
    return m.group() if m else ""

def resolve_iata(ekitan_name):
    """Resolve ekitan airport name to IATA code"""
    if ekitan_name in EKITAN_NAME_TO_IATA:
        return EKITAN_NAME_TO_IATA[ekitan_name]
    # Try partial matching
    for name, iata in EKITAN_NAME_TO_IATA.items():
        if name in ekitan_name or ekitan_name in name:
            return iata
    return None

def fetch_departure_page(ekitan_id):
    """Fetch departure timetable page for an airport"""
    url = f"https://ekitan.com/timetable/airplane/domestic/departure/all/{ekitan_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
        return ""

def parse_flights(html, dep_iata, dep_name):
    """Parse flight entries from HTML"""
    flights = []
    for match in FLIGHT_PATTERN.finditer(html):
        airline_class, dep_time, dep_airport, arr_time, arr_airport, flight_cell = match.groups()
        flight_num = re.sub(r"<.*?>", "", flight_cell).strip()

        if not is_relevant_flight(flight_num):
            continue

        arr_iata = resolve_iata(arr_airport)
        if arr_iata is None:
            print(f"  WARNING: Unknown airport '{arr_airport}' for flight {flight_num}", file=sys.stderr)
            continue

        # Get the short name for the arrival airport
        arr_name = arr_airport
        for name, iata in EKITAN_NAME_TO_IATA.items():
            if iata == arr_iata:
                # Use the canonical short name from EKITAN_AIRPORTS
                for eid, (a_iata, a_name, a_full, a_region) in EKITAN_AIRPORTS.items():
                    if a_iata == arr_iata:
                        arr_name = a_name
                        break
                break

        airline = get_airline_from_flight(flight_num)

        flights.append({
            "flightNumber": flight_num,
            "airline": airline,
            "departure": {
                "airport": dep_name,
                "airportCode": dep_iata,
                "time": dep_time
            },
            "arrival": {
                "airport": arr_name,
                "airportCode": arr_iata,
                "time": arr_time
            },
            "operatingDays": [1, 2, 3, 4, 5, 6, 7]
        })
    return flights

def main():
    all_flights = []
    seen_flights = set()  # (flightNumber, dep_time) for dedup

    airports_to_scrape = sorted(EKITAN_AIRPORTS.keys())
    total = len(airports_to_scrape)

    for i, ekitan_id in enumerate(airports_to_scrape):
        iata, name, fullname, region = EKITAN_AIRPORTS[ekitan_id]
        print(f"[{i+1}/{total}] Fetching {name} ({iata}, ekitan_id={ekitan_id})...", file=sys.stderr)

        html = fetch_departure_page(ekitan_id)
        if not html:
            continue

        flights = parse_flights(html, iata, name)

        added = 0
        for f in flights:
            key = (f["flightNumber"], f["departure"]["time"])
            if key not in seen_flights:
                seen_flights.add(key)
                all_flights.append(f)
                added += 1

        print(f"  Found {len(flights)} relevant flights, added {added} new", file=sys.stderr)
        time.sleep(0.3)  # Rate limiting

    # Sort by airline, then flight number
    all_flights.sort(key=lambda f: (f["airline"], f["flightNumber"], f["departure"]["time"]))

    # Collect all airports that appear in flights
    airport_codes_used = set()
    for f in all_flights:
        airport_codes_used.add(f["departure"]["airportCode"])
        airport_codes_used.add(f["arrival"]["airportCode"])

    # Build airports list
    airports = []
    for eid, (iata, name, fullname, region) in sorted(EKITAN_AIRPORTS.items(), key=lambda x: x[1][0]):
        if iata in airport_codes_used:
            airports.append({
                "code": iata,
                "name": name,
                "fullName": fullname,
                "region": region
            })

    # Sort airports by region order
    REGION_ORDER = ["北海道", "東北", "関東", "中部", "近畿", "中国", "四国", "九州", "沖縄"]
    airports.sort(key=lambda a: (REGION_ORDER.index(a["region"]) if a["region"] in REGION_ORDER else 99, a["code"]))

    print(f"\nTotal flights: {len(all_flights)}", file=sys.stderr)
    print(f"Total airports used: {len(airport_codes_used)}", file=sys.stderr)
    print(f"Airlines: {sorted(set(f['airline'] for f in all_flights))}", file=sys.stderr)

    # Output directory (default: script's directory)
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

    # Output timetable.json
    timetable = {"flights": all_flights}
    with open(os.path.join(out_dir, "timetable.json"), "w", encoding="utf-8") as f:
        json.dump(timetable, f, ensure_ascii=False, indent=2)

    # Output airports.json
    airports_data = {"airports": airports}
    with open(os.path.join(out_dir, "airports.json"), "w", encoding="utf-8") as f:
        json.dump(airports_data, f, ensure_ascii=False, indent=2)

    # Output timetable_meta.json (version = YYYYMMDD)
    from datetime import date
    today = date.today()
    meta = {
        "version": int(today.strftime("%Y%m%d")),
        "validFrom": today.strftime("%Y-%m-01"),
        "validTo": f"{today.year}-{'07' if today.month <= 6 else '12'}-{'31' if today.month > 6 else '30'}",
        "flightCount": len(all_flights)
    }
    with open(os.path.join(out_dir, "timetable_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to {out_dir}/", file=sys.stderr)

if __name__ == "__main__":
    main()
