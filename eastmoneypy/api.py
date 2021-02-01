import logging

import demjson
import requests
from requests import Response

from eastmoneypy import my_env

logger = logging.getLogger(__name__)


def chrome_copy_header_to_dict(src):
    lines = src.split('\n')
    header = {}
    if lines:
        for line in lines:
            try:
                index = line.index(':')
                key = line[:index]
                value = line[index + 1:]
                if key and value:
                    header.setdefault(key.strip(), value.strip())
            except Exception:
                pass
    return header


HEADER = chrome_copy_header_to_dict(my_env['header'])

APIKEY = my_env['appkey']


def parse_resp(resp: Response, key=None):
    if resp.status_code != 200:
        raise Exception(f'code:{resp.status_code},msg:{resp.content}')
    # {
    #   "re": true,
    #   "message": "",
    #   "result": {}
    # }
    result = resp.text
    js_text = result[result.index('(') + 1:result.index(')')]

    ret = demjson.decode(js_text)
    logger.info(f'ret:{ret}')
    data = ret.get('data')
    if data and key:
        result_value = data.get(key)
    else:
        result_value = data

    return ret['state'], result_value


def create_group(group_name):
    url = f'http://myfavor.eastmoney.com/v4/webouter/ag?appkey={APIKEY}&cb=jQuery112404771026622113468_1612176493845&gn={group_name}&_=1612176493849'
    resp = requests.get(url, headers=HEADER)

    _, group = parse_resp(resp)
    return group


def get_groups():
    url = f'http://myfavor.eastmoney.com/v4/webouter/ggdefstkindexinfos?appkey={APIKEY}&cb=jQuery112407703233916827181_1612173986286&g=1&_=1612173986288'

    resp = requests.get(url, headers=HEADER)

    _, value = parse_resp(resp, key='ginfolist')
    return value


def rename_group(group_id, group_name):
    url = f'http://myfavor.eastmoney.com/v4/webouter/mg?appkey={APIKEY}&cb=jQuery112406922055532444666_1612177151715&g={group_id}&gn={group_name}&_=1612177151728'

    resp = requests.get(url, headers=HEADER)

    ret, _ = parse_resp(resp)
    return ret


def del_group(group_name=None, group_id=None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name)
        if not group_id:
            raise Exception(f'could not find group:{group_name}')

    url = f'http://myfavor.eastmoney.com/v4/webouter/dg?appkey={APIKEY}&cb=jQuery1124005355240135242356_1612173048874&g={group_id}&_=1612173048950'

    resp = requests.get(url, headers=HEADER)

    ret, _ = parse_resp(resp, key=None)
    return ret


def get_group_id(group_name):
    groups = get_groups()
    groups = [group for group in groups if group['gname'] == group_name]
    if groups:
        return groups[0]['gid']
    return None


def add_to_group(code, entity_type='stock', group_name=None, group_id=None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name)
        if not group_id:
            raise Exception(f'could not find group:{group_name}')
    code = to_eastmoney_code(code, entity_type=entity_type)
    url = f'http://myfavor.eastmoney.com/v4/webouter/as?appkey={APIKEY}&cb=jQuery112404771026622113468_1612176493843&g={group_id}&sc={code}&_=1612176493913'
    resp = requests.get(url, headers=HEADER)

    return parse_resp(resp)


def to_eastmoney_code(code, entity_type='stock'):
    if entity_type == 'stock':
        # 上海
        if code >= '333333':
            return f'1%24{code}'
        else:
            return f'0%24{code}'


__all__ = ['create_group', 'get_groups', 'rename_group', 'del_group', 'add_to_group', 'to_eastmoney_code']

if __name__ == '__main__':
    groups = get_groups()
    print(groups)

    print(get_group_id('bull'))

    del_group('bull')

    g = create_group('bull')
    print(g)

    print(add_to_group('000999', group_name='bull'))
    print(add_to_group('688001', group_name='bull'))
