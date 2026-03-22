from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory
from lunar_python import Lunar, Solar

try:
    from flask_cors import CORS
except ImportError:
    CORS = None  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR))
if CORS is not None:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

PROVINCES = {
    "beijing": {
        "name": "北京", "cities": {
            "beijing": {"name": "北京", "longitude": 116.41}
        }
    },
    "tianjin": {
        "name": "天津", "cities": {
            "tianjin": {"name": "天津", "longitude": 117.20}
        }
    },
    "shanghai": {
        "name": "上海", "cities": {
            "shanghai": {"name": "上海", "longitude": 121.47}
        }
    },
    "chongqing": {
        "name": "重庆", "cities": {
            "chongqing": {"name": "重庆", "longitude": 106.55}
        }
    },
    "hebei": {
        "name": "河北", "cities": {
            "shijiazhuang": {"name": "石家庄", "longitude": 114.51},
            "tangshan": {"name": "唐山", "longitude": 118.18},
            "baoding": {"name": "保定", "longitude": 115.47},
            "handan": {"name": "邯郸", "longitude": 114.49},
        }
    },
    "shanxi": {
        "name": "山西", "cities": {
            "taiyuan": {"name": "太原", "longitude": 112.55},
            "datong": {"name": "大同", "longitude": 113.30},
            "linfen": {"name": "临汾", "longitude": 111.52},
        }
    },
    "liaoning": {
        "name": "辽宁", "cities": {
            "shenyang": {"name": "沈阳", "longitude": 123.43},
            "dalian": {"name": "大连", "longitude": 121.62},
            "anshan": {"name": "鞍山", "longitude": 122.99},
        }
    },
    "jilin": {
        "name": "吉林", "cities": {
            "changchun": {"name": "长春", "longitude": 125.32},
            "jilin_city": {"name": "吉林", "longitude": 126.55},
        }
    },
    "heilongjiang": {
        "name": "黑龙江", "cities": {
            "haerbin": {"name": "哈尔滨", "longitude": 126.63},
            "daqing": {"name": "大庆", "longitude": 125.10},
            "qiqihaer": {"name": "齐齐哈尔", "longitude": 123.97},
        }
    },
    "jiangsu": {
        "name": "江苏", "cities": {
            "nanjing": {"name": "南京", "longitude": 118.78},
            "suzhou": {"name": "苏州", "longitude": 120.62},
            "wuxi": {"name": "无锡", "longitude": 120.31},
            "changzhou": {"name": "常州", "longitude": 119.97},
            "nantong": {"name": "南通", "longitude": 120.86},
            "xuzhou": {"name": "徐州", "longitude": 117.18},
        }
    },
    "zhejiang": {
        "name": "浙江", "cities": {
            "hangzhou": {"name": "杭州", "longitude": 120.16},
            "ningbo": {"name": "宁波", "longitude": 121.55},
            "wenzhou": {"name": "温州", "longitude": 120.65},
            "jiaxing": {"name": "嘉兴", "longitude": 120.76},
            "jinhua": {"name": "金华", "longitude": 119.65},
        }
    },
    "anhui": {
        "name": "安徽", "cities": {
            "hefei": {"name": "合肥", "longitude": 117.27},
            "wuhu": {"name": "芜湖", "longitude": 118.38},
            "bengbu": {"name": "蚌埠", "longitude": 117.39},
        }
    },
    "fujian": {
        "name": "福建", "cities": {
            "fuzhou": {"name": "福州", "longitude": 119.30},
            "xiamen": {"name": "厦门", "longitude": 118.10},
            "quanzhou": {"name": "泉州", "longitude": 118.59},
            "zhangzhou": {"name": "漳州", "longitude": 117.65},
            "putian": {"name": "莆田", "longitude": 119.01},
            "nanping": {"name": "南平", "longitude": 118.18},
            "longyan": {"name": "龙岩", "longitude": 117.03},
            "sanming": {"name": "三明", "longitude": 117.64},
            "ningde": {"name": "宁德", "longitude": 119.53},
        }
    },
    "jiangxi": {
        "name": "江西", "cities": {
            "nanchang": {"name": "南昌", "longitude": 115.86},
            "jiujiang": {"name": "九江", "longitude": 115.99},
            "ganzhou": {"name": "赣州", "longitude": 114.94},
        }
    },
    "shandong": {
        "name": "山东", "cities": {
            "jinan": {"name": "济南", "longitude": 117.00},
            "qingdao": {"name": "青岛", "longitude": 120.33},
            "yantai": {"name": "烟台", "longitude": 121.39},
            "weifang": {"name": "潍坊", "longitude": 119.16},
            "linyi": {"name": "临沂", "longitude": 118.36},
        }
    },
    "henan": {
        "name": "河南", "cities": {
            "zhengzhou": {"name": "郑州", "longitude": 113.65},
            "luoyang": {"name": "洛阳", "longitude": 112.43},
            "kaifeng": {"name": "开封", "longitude": 114.35},
            "nanyang": {"name": "南阳", "longitude": 112.53},
        }
    },
    "hubei": {
        "name": "湖北", "cities": {
            "wuhan": {"name": "武汉", "longitude": 114.31},
            "yichang": {"name": "宜昌", "longitude": 111.29},
            "xiangyang": {"name": "襄阳", "longitude": 112.14},
        }
    },
    "hunan": {
        "name": "湖南", "cities": {
            "changsha": {"name": "长沙", "longitude": 112.94},
            "zhuzhou": {"name": "株洲", "longitude": 113.13},
            "hengyang": {"name": "衡阳", "longitude": 112.57},
            "yueyang": {"name": "岳阳", "longitude": 113.13},
        }
    },
    "guangdong": {
        "name": "广东", "cities": {
            "guangzhou": {"name": "广州", "longitude": 113.26},
            "shenzhen": {"name": "深圳", "longitude": 114.06},
            "dongguan": {"name": "东莞", "longitude": 113.75},
            "foshan": {"name": "佛山", "longitude": 113.12},
            "zhuhai": {"name": "珠海", "longitude": 113.58},
            "huizhou": {"name": "惠州", "longitude": 114.42},
            "zhongshan": {"name": "中山", "longitude": 113.38},
            "shantou": {"name": "汕头", "longitude": 116.68},
        }
    },
    "guangxi": {
        "name": "广西", "cities": {
            "nanning": {"name": "南宁", "longitude": 108.32},
            "guilin": {"name": "桂林", "longitude": 110.29},
            "liuzhou": {"name": "柳州", "longitude": 109.41},
        }
    },
    "hainan": {
        "name": "海南", "cities": {
            "haikou": {"name": "海口", "longitude": 110.35},
            "sanya": {"name": "三亚", "longitude": 109.51},
        }
    },
    "sichuan": {
        "name": "四川", "cities": {
            "chengdu": {"name": "成都", "longitude": 104.07},
            "mianyang": {"name": "绵阳", "longitude": 104.73},
            "deyang": {"name": "德阳", "longitude": 104.40},
            "yibin": {"name": "宜宾", "longitude": 104.64},
        }
    },
    "guizhou": {
        "name": "贵州", "cities": {
            "guiyang": {"name": "贵阳", "longitude": 106.71},
            "zunyi": {"name": "遵义", "longitude": 106.93},
        }
    },
    "yunnan": {
        "name": "云南", "cities": {
            "kunming": {"name": "昆明", "longitude": 102.73},
            "dali": {"name": "大理", "longitude": 100.23},
        }
    },
    "shaanxi_province": {
        "name": "陕西", "cities": {
            "xian": {"name": "西安", "longitude": 108.94},
            "xianyang": {"name": "咸阳", "longitude": 108.71},
            "baoji": {"name": "宝鸡", "longitude": 107.14},
        }
    },
    "gansu": {
        "name": "甘肃", "cities": {
            "lanzhou": {"name": "兰州", "longitude": 103.83},
        }
    },
    "qinghai": {
        "name": "青海", "cities": {
            "xining": {"name": "西宁", "longitude": 101.77},
        }
    },
    "neimenggu": {
        "name": "内蒙古", "cities": {
            "huhehaote": {"name": "呼和浩特", "longitude": 111.75},
            "baotou": {"name": "包头", "longitude": 109.84},
        }
    },
    "xizang": {
        "name": "西藏", "cities": {
            "lasa": {"name": "拉萨", "longitude": 91.13},
        }
    },
    "ningxia": {
        "name": "宁夏", "cities": {
            "yinchuan": {"name": "银川", "longitude": 106.23},
        }
    },
    "xinjiang": {
        "name": "新疆", "cities": {
            "wulumuqi": {"name": "乌鲁木齐", "longitude": 87.62},
            "kashi": {"name": "喀什", "longitude": 75.99},
        }
    },
    "hongkong": {
        "name": "香港", "cities": {
            "hongkong": {"name": "香港", "longitude": 114.17}
        }
    },
    "macao": {
        "name": "澳门", "cities": {
            "macao": {"name": "澳门", "longitude": 113.54}
        }
    },
    "taiwan": {
        "name": "台湾", "cities": {
            "taipei": {"name": "台北", "longitude": 121.57},
            "kaohsiung": {"name": "高雄", "longitude": 120.31},
            "taichung": {"name": "台中", "longitude": 120.68},
        }
    },
}

OVERSEAS = {
    "us": {
        "name": "美国", "cities": {
            "newyork": {"name": "纽约", "longitude": -74.01, "utc_offset": -5},
            "losangeles": {"name": "洛杉矶", "longitude": -118.24, "utc_offset": -8},
            "chicago": {"name": "芝加哥", "longitude": -87.63, "utc_offset": -6},
            "houston": {"name": "休斯顿", "longitude": -95.37, "utc_offset": -6},
            "sanfrancisco": {"name": "旧金山", "longitude": -122.42, "utc_offset": -8},
            "seattle": {"name": "西雅图", "longitude": -122.33, "utc_offset": -8},
        }
    },
    "uk": {
        "name": "英国", "cities": {
            "london": {"name": "伦敦", "longitude": -0.12, "utc_offset": 0},
            "manchester": {"name": "曼彻斯特", "longitude": -2.24, "utc_offset": 0},
        }
    },
    "japan": {
        "name": "日本", "cities": {
            "tokyo": {"name": "东京", "longitude": 139.69, "utc_offset": 9},
            "osaka": {"name": "大阪", "longitude": 135.50, "utc_offset": 9},
        }
    },
    "korea": {
        "name": "韩国", "cities": {
            "seoul": {"name": "首尔", "longitude": 126.98, "utc_offset": 9},
            "busan": {"name": "釜山", "longitude": 129.08, "utc_offset": 9},
        }
    },
    "singapore": {
        "name": "新加坡", "cities": {
            "singapore": {"name": "新加坡", "longitude": 103.82, "utc_offset": 8},
        }
    },
    "malaysia": {
        "name": "马来西亚", "cities": {
            "kualalumpur": {"name": "吉隆坡", "longitude": 101.69, "utc_offset": 8},
        }
    },
    "thailand": {
        "name": "泰国", "cities": {
            "bangkok": {"name": "曼谷", "longitude": 100.50, "utc_offset": 7},
        }
    },
    "vietnam": {
        "name": "越南", "cities": {
            "hanoi": {"name": "河内", "longitude": 105.85, "utc_offset": 7},
            "hochiminh": {"name": "胡志明市", "longitude": 106.63, "utc_offset": 7},
        }
    },
    "australia": {
        "name": "澳大利亚", "cities": {
            "sydney": {"name": "悉尼", "longitude": 151.21, "utc_offset": 10},
            "melbourne": {"name": "墨尔本", "longitude": 144.96, "utc_offset": 10},
        }
    },
    "canada": {
        "name": "加拿大", "cities": {
            "toronto": {"name": "多伦多", "longitude": -79.38, "utc_offset": -5},
            "vancouver": {"name": "温哥华", "longitude": -123.12, "utc_offset": -8},
        }
    },
    "germany": {
        "name": "德国", "cities": {
            "berlin": {"name": "柏林", "longitude": 13.40, "utc_offset": 1},
            "munich": {"name": "慕尼黑", "longitude": 11.58, "utc_offset": 1},
        }
    },
    "france": {
        "name": "法国", "cities": {
            "paris": {"name": "巴黎", "longitude": 2.35, "utc_offset": 1},
        }
    },
    "russia": {
        "name": "俄罗斯", "cities": {
            "moscow": {"name": "莫斯科", "longitude": 37.62, "utc_offset": 3},
        }
    },
    "india": {
        "name": "印度", "cities": {
            "newdelhi": {"name": "新德里", "longitude": 77.21, "utc_offset": 5.5},
            "mumbai": {"name": "孟买", "longitude": 72.88, "utc_offset": 5.5},
        }
    },
    "uae": {
        "name": "阿联酋", "cities": {
            "dubai": {"name": "迪拜", "longitude": 55.27, "utc_offset": 4},
        }
    },
    "indonesia": {
        "name": "印度尼西亚", "cities": {
            "jakarta": {"name": "雅加达", "longitude": 106.85, "utc_offset": 7},
        }
    },
    "philippines": {
        "name": "菲律宾", "cities": {
            "manila": {"name": "马尼拉", "longitude": 120.98, "utc_offset": 8},
        }
    },
    "newzealand": {
        "name": "新西兰", "cities": {
            "auckland": {"name": "奥克兰", "longitude": 174.76, "utc_offset": 12},
        }
    },
}


def _apply_true_solar(dt, longitude, utc_offset=8.0):
    standard_meridian = utc_offset * 15.0
    minutes_offset = int(round((longitude - standard_meridian) * 4))
    return dt + timedelta(minutes=minutes_offset)


def build_bazi_result(
    input_datetime: str,
    time_mode: str = "standard",
    longitude: Optional[float] = None,
    utc_offset: Optional[float] = None,
    location_label: Optional[str] = None,
    gender: int = 1,
    sect: int = 2,
) -> dict:
    dt = datetime.strptime(input_datetime, "%Y-%m-%dT%H:%M")
    calc_dt = _apply_true_solar(dt, longitude, utc_offset) if time_mode == "true_solar" and longitude is not None else dt
    solar = Solar.fromYmdHms(calc_dt.year, calc_dt.month, calc_dt.day, calc_dt.hour, calc_dt.minute, calc_dt.second)
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()
    yun = eight_char.getYun(gender, sect)

    da_yun_list = []
    xiao_yun_list = []
    for item in yun.getDaYun(14):
        if not item.getGanZhi():
            for x in item.getXiaoYun(10):
                xiao_yun_list.append({"year": x.getYear(), "age": x.getAge(), "gan_zhi": x.getGanZhi()})
            continue
        if item.getStartAge() > 120:
            break
        span = max(1, item.getEndYear() - item.getStartYear() + 1)
        liu_nian = item.getLiuNian(min(10, span))
        da_yun_list.append({
            "gan_zhi": item.getGanZhi(),
            "start_year": item.getStartYear(),
            "end_year": item.getEndYear(),
            "start_age": item.getStartAge(),
            "end_age": min(item.getEndAge(), 120),
            "liu_nian": [{"year": n.getYear(), "gan_zhi": n.getGanZhi()} for n in liu_nian],
        })

    return {
        "solar_datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "calc_datetime": calc_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "time_mode": time_mode,
        "longitude": longitude,
        "utc_offset": utc_offset,
        "location_label": location_label,
        "lunar_date": lunar.toString(),
        "bazi": f"{eight_char.getYear()} {eight_char.getMonth()} {eight_char.getDay()} {eight_char.getTime()}",
        "year_pillar": eight_char.getYear(),
        "month_pillar": eight_char.getMonth(),
        "day_pillar": eight_char.getDay(),
        "time_pillar": eight_char.getTime(),
        "yun": {
            "gender": gender,
            "sect": sect,
            "start_year": yun.getStartYear(),
            "start_month": yun.getStartMonth(),
            "start_day": yun.getStartDay(),
            "start_solar": yun.getStartSolar().toYmdHms(),
            "xiao_yun": xiao_yun_list,
            "da_yun": da_yun_list,
        },
    }


def build_bazi_from_lunar(
    lunar_year: int,
    lunar_month: int,
    lunar_day: int,
    hour: int = 0,
    minute: int = 0,
    is_leap_month: bool = False,
    time_mode: str = "standard",
    longitude: Optional[float] = None,
    utc_offset: Optional[float] = None,
    location_label: Optional[str] = None,
    gender: int = 1,
    sect: int = 2,
) -> dict:
    month_val = -abs(lunar_month) if is_leap_month else lunar_month
    lunar = Lunar.fromYmdHms(lunar_year, month_val, lunar_day, hour, minute, 0)
    solar = lunar.getSolar()
    solar_dt_str = f"{solar.getYear():04d}-{solar.getMonth():02d}-{solar.getDay():02d}T{hour:02d}:{minute:02d}"
    return build_bazi_result(
        solar_dt_str,
        time_mode=time_mode,
        longitude=longitude,
        utc_offset=utc_offset,
        location_label=location_label,
        gender=gender,
        sect=sect,
    )


def build_bazi_from_pillars(
    year_pillar: str,
    month_pillar: str,
    day_pillar: str,
    time_pillar: str,
    sect: int = 2,
    base_year: int = 1900,
) -> dict:
    solar_list = Solar.fromBaZi(year_pillar, month_pillar, day_pillar, time_pillar, sect, base_year)
    candidates = [
        f"{s.getYear():04d}-{s.getMonth():02d}-{s.getDay():02d} {s.getHour():02d}:{s.getMinute():02d}:{s.getSecond():02d}"
        for s in solar_list
        if 1900 <= s.getYear() <= 2100
    ]
    return {
        "bazi": f"{year_pillar} {month_pillar} {day_pillar} {time_pillar}",
        "candidates": candidates,
        "count": len(candidates),
        "sect": sect,
        "base_year": base_year,
    }


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/config.js")
def spa_config():
    return send_from_directory(FRONTEND_DIR, "config.js")


@app.route("/ai-fortune/<path:filename>")
def ai_fortune_static(filename: str):
    return send_from_directory(FRONTEND_DIR / "ai-fortune", filename)


@app.route("/api/locations")
def get_locations():
    provinces = []
    for pk, pv in PROVINCES.items():
        cities = [{"code": ck, "name": cv["name"]} for ck, cv in pv["cities"].items()]
        provinces.append({"code": pk, "name": pv["name"], "cities": cities})
    countries = []
    for ck, cv in OVERSEAS.items():
        cities = [{"code": cc, "name": ccv["name"]} for cc, ccv in cv["cities"].items()]
        countries.append({"code": ck, "name": cv["name"], "cities": cities})
    return jsonify({"provinces": provinces, "countries": countries})


@app.route("/api/bazi", methods=["POST"])
def get_bazi():
    payload = request.get_json(silent=True) or {}
    mode = payload.get("mode", "datetime")

    try:
        if mode == "datetime":
            input_datetime = payload.get("datetime")
            time_mode = payload.get("timeMode", "standard")
            location_type = payload.get("locationType", "domestic")
            gender = int(payload.get("gender", 1))
            sect = int(payload.get("sect", 2))
            longitude_value = None
            utc_offset = 8.0
            location_label = None

            if location_type == "domestic":
                province_code = payload.get("province", "")
                city_code = payload.get("city", "")
                province = PROVINCES.get(province_code)
                if province is None:
                    return jsonify({"error": "无效的省份"}), 400
                city = province["cities"].get(city_code)
                if city is None:
                    return jsonify({"error": "无效的城市"}), 400
                longitude_value = city["longitude"]
                location_label = f"{province['name']}{city['name']}"
            elif location_type == "overseas":
                country_code = payload.get("country", "")
                city_code = payload.get("city", "")
                country = OVERSEAS.get(country_code)
                if country is None:
                    return jsonify({"error": "无效的国家"}), 400
                city = country["cities"].get(city_code)
                if city is None:
                    return jsonify({"error": "无效的城市"}), 400
                longitude_value = city["longitude"]
                utc_offset = city["utc_offset"]
                location_label = f"{country['name']}{city['name']}"
            else:
                return jsonify({"error": "无效的地址类型"}), 400

            if not input_datetime:
                return jsonify({"error": "请输入出生日期时间"}), 400
            try:
                dt_solar = datetime.strptime(input_datetime, "%Y-%m-%dT%H:%M")
            except ValueError:
                return jsonify({"error": "请输入出生日期时间"}), 400
            if not (1900 <= dt_solar.year <= 2100):
                return jsonify({"error": "请输入1900-2100之间的年份"}), 400
            result = build_bazi_result(
                input_datetime,
                time_mode=time_mode,
                longitude=longitude_value,
                utc_offset=utc_offset,
                location_label=location_label,
                gender=gender,
                sect=sect,
            )
        elif mode == "lunar":
            lunar_year = int(payload.get("lunarYear"))
            lunar_month = int(payload.get("lunarMonth"))
            lunar_day = int(payload.get("lunarDay"))
            hour = int(payload.get("hour", 0))
            minute = int(payload.get("minute", 0))
            is_leap_month = bool(payload.get("isLeapMonth", False))
            time_mode = payload.get("timeMode", "standard")
            location_type = payload.get("locationType", "domestic")
            gender = int(payload.get("gender", 1))
            sect = int(payload.get("sect", 2))
            longitude_value = None
            utc_offset = 8.0
            location_label = None

            if location_type == "domestic":
                province_code = payload.get("province", "")
                city_code = payload.get("city", "")
                province = PROVINCES.get(province_code)
                if province is None:
                    return jsonify({"error": "无效的省份"}), 400
                city = province["cities"].get(city_code)
                if city is None:
                    return jsonify({"error": "无效的城市"}), 400
                longitude_value = city["longitude"]
                location_label = f"{province['name']}{city['name']}"
            elif location_type == "overseas":
                country_code = payload.get("country", "")
                city_code = payload.get("city", "")
                country = OVERSEAS.get(country_code)
                if country is None:
                    return jsonify({"error": "无效的国家"}), 400
                city = country["cities"].get(city_code)
                if city is None:
                    return jsonify({"error": "无效的城市"}), 400
                longitude_value = city["longitude"]
                utc_offset = city["utc_offset"]
                location_label = f"{country['name']}{city['name']}"
            else:
                return jsonify({"error": "无效的地址类型"}), 400

            result = build_bazi_from_lunar(
                lunar_year, lunar_month, lunar_day, hour, minute,
                is_leap_month=is_leap_month,
                time_mode=time_mode,
                longitude=longitude_value,
                utc_offset=utc_offset,
                location_label=location_label,
                gender=gender,
                sect=sect,
            )
        elif mode == "pillars":
            year_pillar = payload.get("yearPillar", "").strip()
            month_pillar = payload.get("monthPillar", "").strip()
            day_pillar = payload.get("dayPillar", "").strip()
            time_pillar = payload.get("timePillar", "").strip()
            sect = int(payload.get("sect", 2))
            base_year = int(payload.get("baseYear", 1900))

            if not all([year_pillar, month_pillar, day_pillar, time_pillar]):
                return jsonify({"error": "请完整输入四柱"}), 400

            result = build_bazi_from_pillars(year_pillar, month_pillar, day_pillar, time_pillar, sect=sect, base_year=base_year)
        else:
            return jsonify({"error": "无效的模式"}), 400
    except ValueError:
        return jsonify({"error": "请输入1900-2100之间的年份"}), 400
    except Exception as exc:
        return jsonify({"error": f"排盘失败: {exc}"}), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
