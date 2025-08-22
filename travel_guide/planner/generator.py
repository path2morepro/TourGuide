from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import os
import requests
from collections import defaultdict
from travel_guide.rag import llm
import json

load_dotenv()

def query_weather(destination, target_date, days):
    # 获取城市地理信息
    api_key= os.environ.get("WEATHER_API_KEY")
    city_url = f"http://api.openweathermap.org/geo/1.0/direct?q={destination}&limit={5}&appid={api_key}"
    response = requests.get(city_url)
    if response.status_code != 200:
        raise Exception(f"请求失败：{response.status_code} {response.text}")
    city = response.json()[0]
    lat = city["lat"]
    lon = city["lon"]

    # 你要哪一天的预报？
    temper_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"
    response = requests.get(temper_url)
    if response.status_code != 200:
        raise Exception(f"请求失败：{response.status_code} {response.text}")
    
    weather = response.json()
    # 从start date 开始到start date + days 结束期间的天气信息
    # 重点提取下雨信息，高温信息， 低温信息
    forecast_list = weather['list']

    # 但是我们需要的是target_date + days的天气，如果不在这个范围内我们要返回别的东西
    target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    future_day = target_date + timedelta(days=days)
    
    filtered = [
    item for item in forecast_list
    if target_date <= datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S").date() < future_day]
    
    if not filtered:
        return {}
    
    daily_info = defaultdict(lambda: {'temps': [], 'weather': set()})

    for entry in filtered:
        dt_txt = entry['dt_txt']  # e.g., "2025-07-12 15:00:00"
        date = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").date()

        temp_celsius = entry['main']['temp'] - 273.15
        weather_main = entry['weather'][0]['main'].lower()

        daily_info[date]['temps'].append(temp_celsius)
        daily_info[date]['weather'].add(weather_main)

    # 初始化结果集
    hot_days = []
    cold_days = []
    wet_days = []

    # 分析每一天的汇总信息
    # 这个分析汇总可能会需要改一下
    for date, info in daily_info.items():
        max_temp = max(info['temps'])
        min_temp = min(info['temps'])

        if max_temp > 25:
            hot_days.append(date)
        if min_temp < -5:
            cold_days.append(date)
        if 'rain' in info['weather'] or 'snow' in info['weather']:
            wet_days.append(date)

    return {"hot": hot_days, "cold": cold_days, "wet": wet_days}

def suggest_transport(trip_info):
    # 从环境变量获取 API 凭证
    client_id = os.environ.get("AIR_API_KEY")
    client_secret = os.environ.get("AIR_API_SECRET")

    if not client_id or not client_secret:
        raise ValueError("未找到 AIR_API_KEY 或 AIR_API_SECRET，请确认 .env 文件配置")

    # Step 1: 获取 access_token
    token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    token_res = requests.post(token_url, headers=headers, data=data)
    # ?
    token_res.raise_for_status()
    #  =if token_res.status_code >= 400:
    # raise Exception("请求失败")
    access_token = token_res.json()["access_token"]

    # Step 2: 调用航班搜索接口
    search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    search_headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "originLocationCode": get_iata(trip_info["origin"]),
        "destinationLocationCode": get_iata(trip_info["destination"]),
        "departureDate": trip_info["date"],
        "adults": 1,
        "max": 10
    }
    response = requests.get(search_url, headers=search_headers, params=params)
    response.raise_for_status()
    offers = response.json().get("data", [])

    # Step 3: 提取关键信息
    results = []
    for offer in offers:
        price = offer.get("price", {}).get("total")
        currency = offer.get("price", {}).get("currency", "EUR")
        itinerary = offer.get("itineraries", [])[0]
        segments = itinerary.get("segments", [])

        first = segments[0]
        last = segments[-1]

        flight_info = {
            "price": f"{price} {currency}",
            "duration": itinerary.get("duration", ""),
            "from": first["departure"]["iataCode"],
            "to": last["arrival"]["iataCode"],
            "departure_time": first["departure"]["at"],
            "arrival_time": last["arrival"]["at"],
            "stops": len(segments) - 1,
            "carriers": [seg["carrierCode"] for seg in segments],
            "flight_numbers": [f'{seg["carrierCode"]} {seg["number"]}' for seg in segments],
        }
        results.append(flight_info)

    return results


def suggest_hotels(location, start_date, end_date):
    url = "https://engine.hotellook.com/api/v2/cache.json"
    params = {
        "location": location,
        "checkIn": start_date,
        "checkOut": end_date,
        "currency": "EUR",
        "limit": 20
    }

    response = requests.get(url, params=params).json()
    hotels = []
    for hotel in response:
        hotels.append({
            "hotel_name": hotel.get("hotelName"),
            "stars": hotel.get("stars"),
            "price_from": hotel.get("priceFrom"),
            # "city": hotel.get("location", {}).get("name"),
            # "country": hotel.get("location", {}).get("country")
        })
        # print(hotel.get("hotelName"))
        # print(hotel.get("priceFrom")) 
    # 后面可以拿着这些信息去做筛选，当然是给llm
    return hotels

def get_iata(city):
    CITY_TO_IATA = {
        "Stockholm": "ARN",      # Arlanda Airport
        "Berlin": "BER",         # Berlin Brandenburg
        "Paris": "CDG",          # Charles de Gaulle
        "London": "LHR",         # Heathrow
        "Amsterdam": "AMS",      # Schiphol
        "Copenhagen": "CPH",     # Kastrup
        "Rome": "FCO",           # Fiumicino
        "Madrid": "MAD",         # Barajas
        "Vienna": "VIE",         # Vienna International
        "Oslo": "OSL",           # Gardermoen
        "Helsinki": "HEL",       # Helsinki-Vantaa
        "Zurich": "ZRH",         # Zurich Airport
        "Brussels": "BRU",       # Brussels Airport
        "Lisbon": "LIS",         # Humberto Delgado
        "Prague": "PRG",         # Václav Havel
        "Warsaw": "WAW",         # Chopin Airport
        "Athens": "ATH",         # Eleftherios Venizelos
        "Budapest": "BUD",       # Ferenc Liszt
        "Dublin": "DUB",         # Dublin Airport
        "Munich": "MUC",         # Franz Josef Strauss
        "Frankfurt": "FRA",      # Frankfurt International
        "Barcelona": "BCN",      # El Prat
        "Milan": "MXP",          # Malpensa
        "Nice": "NCE",           # Côte d’Azur
        "Hamburg": "HAM",        # Hamburg Airport
        "Reykjavik": "KEF",      # Keflavík
        "Ljubljana": "LJU",      # Jože Pučnik Airport
        "Tallinn": "TLL",        # Lennart Meri
        "Riga": "RIX",           # Riga International
        "Vilnius": "VNO"         # Vilnius International
    }
    return CITY_TO_IATA.get(city, "")


def suggest_attractions(trip_info):
    destination = trip_info.get("destination", "")
    date = trip_info.get("date", "")
    days = trip_info.get("days", "")
    preferences = trip_info.get("preferences", {})  # dict 类型

    if not isinstance(preferences, dict):
        raise ValueError("preferences 字段不是结构化 dict，请检查数据格式")

    # 构造用户偏好描述
    pref_text = ""
    if preferences.get("attraction"):
        pref_text += f"景点偏好：{preferences['attraction']}\n"
    if preferences.get("food"):
        pref_text += f"饮食偏好：{preferences['food']}\n"
    if preferences.get("hotel"):
        pref_text += f"住宿偏好：{preferences['hotel']}\n"
    if preferences.get("transport"):
        pref_text += f"出行偏好：{preferences['transport']}\n"
    if preferences.get("other"):
        pref_text += f"其他需求：{preferences['other']}\n"

    # 构造提示词（prompt）
    prompt = f"""
你是一个专业旅行推荐助手。用户将从 {date} 开始在 {destination} 游玩 {days} 天。
以下是用户的偏好信息：
{pref_text}

请根据目的地和用户偏好，为用户个性化推荐 3 到 5 个最佳景点。

只输出 JSON 格式的列表，内容仅包含景点名称，不要附加任何解释或介绍。

输出示例：
[
  "景点A",
  "景点B",
  "景点C"
]

严格只输出 JSON。
"""

    response, _ = llm(prompt)
    return response



def suggest_diet(trip_info):
    destination = trip_info.get("destination", "")
    date = trip_info.get("date", "")
    days = trip_info.get("days", "")
    preferences = trip_info.get("preferences", {})  # dict 类型

    if not isinstance(preferences, dict):
        raise ValueError("preferences 字段不是结构化 dict，请检查数据格式")
    
    pref_text = ""
    if preferences.get("attraction"):
        pref_text += f"景点偏好：{preferences['attraction']}\n"
    if preferences.get("food"):
        pref_text += f"饮食偏好：{preferences['food']}\n"
    if preferences.get("accommodation"):
        pref_text += f"住宿偏好：{preferences['accommodation']}\n"
    if preferences.get("transport"):
        pref_text += f"出行偏好：{preferences['transport']}\n"
    if preferences.get("other"):
        pref_text += f"其他需求：{preferences['other']}\n"
    prompt = f"""你是一个专业旅行美食推荐助手。用户将从 {date} 开始在 {destination} 游玩 {days} 天。
以下是用户的偏好信息：
{pref_text}

请根据目的地和用户偏好，为用户个性化推荐 3 到 5 个当地值得尝试的美食或餐厅。

只输出 JSON 格式的列表，内容仅包含名称，不要附加任何说明或描述。

输出示例：
[
"美食/餐厅A",
"美食/餐厅B",
"美食/餐厅C"
]

严格只输出 JSON。
"""

    response, _ = llm(prompt)
    return response



def generate_full_plan(trip_info):
    from travel_guide.rag import llm
    from datetime import datetime, timedelta

    destination = trip_info["destination"]
    origin = trip_info["origin"]
    date = trip_info["date"]
    days = trip_info["days"]
    preferences = trip_info.get("preferences", {})

    # 计算结束日期
    try:
        start_date = datetime.strptime(date, "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=days)
    except Exception:
        start_date, end_date = "未知", "未知"

    # 各模块信息收集
    weather_info = query_weather(destination, date, days)
    flights = suggest_transport(trip_info)
    hotels = suggest_hotels(destination, date, end_date.strftime("%Y-%m-%d"))
    attractions = suggest_attractions(trip_info)
    foods = suggest_diet(trip_info)

    # 构造 prompt
    prompt = f"""
你是一个智能旅行助手，请根据以下信息为用户生成一个为期 {days} 天的旅游计划，包含每天建议游玩内容。

出发地：{origin}
目的地：{destination}
日期：{date} 至 {end_date}
用户偏好：{json.dumps(preferences, ensure_ascii=False)}

天气预报总结：
{weather_info}

推荐航班选项（展示其中几条）：
{json.dumps(flights[:3], ensure_ascii=False)}

推荐住宿：
{json.dumps(hotels[:3], ensure_ascii=False)}

推荐景点：
{attractions}

推荐美食/餐厅：
{foods}

请你根据以上信息，为用户生成结构清晰、节奏合理的每日游玩安排（可按 “第1天、第2天...” 分天写）。
建议结合天气、偏好、时间安排等做智能排序。每一天可包含：上午/下午/晚上安排。

最后简要总结：预计预算范围、适合人群、特别提醒等。

不要包含“以下是您...”这类模板语句，直接进入正文。
"""

    plan_text, _ = llm(prompt)
    return plan_text
