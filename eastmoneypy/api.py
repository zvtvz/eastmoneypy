import logging
import time

import demjson3
import requests
from requests import Response, Session

from eastmoneypy import my_env

logger = logging.getLogger(__name__)


def current_timestamp():
    return int(time.time() * 1000)


def chrome_copy_header_to_dict(src):
    lines = src.split("\n")
    header = {}
    if lines:
        for line in lines:
            try:
                index = line.index(":")
                key = line[:index]
                value = line[index + 1:]
                if key and value:
                    header.setdefault(key.strip(), value.strip())
            except Exception:
                pass
    return header


HEADER = chrome_copy_header_to_dict(my_env["header"])

# 这个其实是api的版本信息，务必使用最新的
# 认证信息其实是在headers里面的cookie中
APIKEY = my_env["appkey"]


def parse_resp(resp: Response, key=None):
    if resp.status_code != 200:
        raise Exception(f"code:{resp.status_code},msg:{resp.content}")
    # {
    #   "re": true,
    #   "message": "",
    #   "result": {}
    # }
    result = resp.text
    js_text = result[result.index("(") + 1: result.index(")")]

    ret = demjson3.decode(js_text)
    logger.debug(f"ret:{ret}")
    data = ret.get("data")
    if data and key:
        result_value = data.get(key)
    else:
        result_value = data

    resp.close()
    return ret["state"], result_value


def create_group(group_name, session: Session = None, api_key: str = APIKEY,
                 headers=None):
    if headers is None:
        headers = HEADER
    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/ag?appkey={api_key}&cb=jQuery112404771026622113468_{ts - 10}&gn={group_name}&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    _, group = parse_resp(resp)
    return group


def get_groups(session: Session = None, api_key: str = APIKEY,
               headers=None):
    if headers is None:
        headers = HEADER
    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/ggdefstkindexinfos?appkey={api_key}&cb=jQuery112407703233916827181_{ts - 10}&g=1&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    _, value = parse_resp(resp, key="ginfolist")
    return value


def rename_group(group_id, group_name, session: Session = None, api_key: str = APIKEY,
                 headers=None):
    if headers is None:
        headers = HEADER
    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/mg?appkey={api_key}&cb=jQuery112406922055532444666_{ts - 10}&g={group_id}&gn={group_name}&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    ret, _ = parse_resp(resp)
    return ret


def del_group(group_name=None, group_id=None, session: Session = None, api_key: str = APIKEY,
              headers=None):
    if headers is None:
        headers = HEADER
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session, api_key=api_key, headers=headers)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")

    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/dg?appkey={api_key}&cb=jQuery1124005355240135242356_{ts - 10}&g={group_id}&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    ret, _ = parse_resp(resp, key=None)
    return ret


def get_group_id(group_name, session=None, api_key: str = APIKEY,
                 headers=None):
    if headers is None:
        headers = HEADER
    groups = get_groups(session=session, api_key=api_key, headers=headers)
    groups = [group for group in groups if group["gname"] == group_name]
    if groups:
        return groups[0]["gid"]
    return None


def list_entities(group_name=None, group_id=None, session: Session = None, api_key: str = APIKEY,
                  headers=None):
    if headers is None:
        headers = HEADER
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session, api_key=api_key, headers=headers)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")

    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/gstkinfos?appkey={api_key}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    _, result = parse_resp(resp)
    datas = result["stkinfolist"]
    return [data["security"].split("$")[1] for data in datas]


def add_to_group(
        code=None, entity_type="stock", entity_id=None, group_name=None, group_id=None, session: Session = None,
        api_key: str = APIKEY,
        headers=None
):
    if code is None and entity_id is None:
        raise Exception("code or entity_id must be set")

    if code is not None and entity_id is not None:
        raise Exception("code and entity_id cannot be both set")

    if headers is None:
        headers = HEADER
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session, api_key=api_key, headers=headers)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")

    if entity_id:
        em_sec_id = to_em_sec_id(entity_id)
    else:
        em_sec_id = to_eastmoney_code(code, entity_type=entity_type)
    ts = current_timestamp()
    url = f"https://myfavor.eastmoney.com/v4/webouter/as?appkey={api_key}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&sc={em_sec_id}&_={ts}"

    if session:
        resp = session.get(url, headers=headers)
    else:
        resp = requests.get(url, headers=headers)

    return parse_resp(resp)


def to_eastmoney_code(code, entity_type="stock"):
    if entity_type == "stock":
        code_ = int(code)
        # 上海
        if 600000 <= code_ <= 800000:
            return f"1%24{code}"
        else:
            return f"0%24{code}"
    if entity_type == "block":
        return f"90${code}"
    if entity_type == "stockhk":
        return f"116%24{code}"
    if entity_type == "stockus":
        return f"105%24{code}"
    assert False


exchange_map_em_flag = {
    #: 深证交易所
    "sz": 0,
    # ":上证交易所
    "sh": 1,
    # ":北交所
    "bj": 0,
    # ":纳斯达克
    "nasdaq": 105,
    # ":纽交所
    "nyse": 106,
    # ":中国金融期货交易所
    "cffex": 8,
    # ":上海期货交易所
    "shfe": 113,
    # ":大连商品交易所
    "dce": 114,
    # ":郑州商品交易所
    "czce": 115,
    # ":上海国际能源交易中心
    "ine": 142,
    # ":港交所
    "hk": 116,
    # ":中国行业/概念板块
    "cn": 90,
    # ":美国指数
    "us": 100,
    # ":汇率
    "forex": 119,
}


def decode_entity_id(entity_id: str):
    """
    decode entity id to entity_type, exchange, code

    :param entity_id:
    :return: tuple with format (entity_type, exchange, code)
    """
    result = entity_id.split("_")
    entity_type = result[0]
    exchange = result[1]
    code = "".join(result[2:])
    return entity_type, exchange, code


def to_em_sec_id(entity_id):
    entity_type, exchange, code = decode_entity_id(entity_id)

    # 主力合约
    if entity_type == "future" and code[-1].isalpha():
        code = code + "m"
    if entity_type == "currency" and "CNYC" in code:
        return f"120%24{code}"
    if entity_type == "block":
        return f"90${code}"

    em_exchange_code = exchange_map_em_flag.get(exchange)
    if em_exchange_code is None:
        raise ValueError(f"Unsupported exchange: {exchange}")
    return f"{em_exchange_code}%24{code}"


__all__ = [
    "create_group",
    "get_groups",
    "rename_group",
    "del_group",
    "get_group_id",
    "add_to_group",
    "list_entities",
    "to_eastmoney_code",
]

if __name__ == "__main__":
    print(add_to_group(entity_id="stock_sh_601162", group_name="自选股"))
    print(add_to_group(entity_id="stock_sz_000777", group_name="自选股"))
    print(add_to_group(entity_id="stock_bj_920002", group_name="自选股"))
    print(add_to_group(entity_id="stockhk_hk_09626", group_name="自选股"))
    print(add_to_group(entity_id="stockus_nyse_CRCL", group_name="自选股"))
    print(add_to_group(entity_id="stockus_nasdaq_NVDA", group_name="自选股"))
