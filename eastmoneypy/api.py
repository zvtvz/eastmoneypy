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
    logger.info(f"ret:{ret}")
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
    url = f"http://myfavor.eastmoney.com/v4/webouter/ag?appkey={api_key}&cb=jQuery112404771026622113468_{ts - 10}&gn={group_name}&_={ts}"

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
    url = f"http://myfavor.eastmoney.com/v4/webouter/ggdefstkindexinfos?appkey={api_key}&cb=jQuery112407703233916827181_{ts - 10}&g=1&_={ts}"

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
    url = f"http://myfavor.eastmoney.com/v4/webouter/mg?appkey={api_key}&cb=jQuery112406922055532444666_{ts - 10}&g={group_id}&gn={group_name}&_={ts}"

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
    url = f"http://myfavor.eastmoney.com/v4/webouter/dg?appkey={api_key}&cb=jQuery1124005355240135242356_{ts - 10}&g={group_id}&_={ts}"

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
        code, entity_type="stock", group_name=None, group_id=None, session: Session = None, api_key: str = APIKEY,
        headers=None
):
    if headers is None:
        headers = HEADER
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name, session=session, api_key=api_key, headers=headers)
        if not group_id:
            raise Exception(f"could not find group:{group_name}")

    code = to_eastmoney_code(code, entity_type=entity_type)
    ts = current_timestamp()
    url = f"http://myfavor.eastmoney.com/v4/webouter/as?appkey={api_key}&cb=jQuery112404771026622113468_{ts - 10}&g={group_id}&sc={code}&_={ts}"

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
    print(get_groups())
    create_group("大局")
    print(add_to_group("MSFT", group_name="大局", entity_type="stockus"))
    print(list_entities(group_name="大局"))
    print(get_group_id(group_name="大局"))
    del_group("大局")
    # find the header in chrome
    headers = chrome_copy_header_to_dict('''
Accept: */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7
Connection: keep-alive
sec-ch-ua-platform: "macOS"
    ''')
    print(get_groups(headers=headers))
    create_group("大局", headers=headers)
    print(add_to_group("MSFT", group_name="大局", entity_type="stockus", headers=headers))
    print(list_entities(group_name="大局", headers=headers))
    print(get_group_id(group_name="大局", headers=headers))
    del_group("大局", headers=headers)
