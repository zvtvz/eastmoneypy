import logging

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


def parse_resp(resp: Response):
    if resp.status_code != 200:
        raise Exception(f'code:{resp.status_code},msg:{resp.content}')
    # {
    #   "re": true,
    #   "message": "",
    #   "result": {}
    # }
    ret = resp.json()
    logger.info(f'ret:{ret}')
    return ret['re'], ret.get('result')


def create_group(group_name):
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/addgroup'
    resp = requests.post(url, headers=HEADER,
                         data={'groupname': group_name})

    return parse_resp(resp)


def get_groups():
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/group'

    resp = requests.get(url, headers=HEADER)

    _, value = parse_resp(resp)
    if value:
        return value['groups']


def rename_group(group_id, group_name):
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/editgroupname'

    resp = requests.post(url, headers=HEADER,
                         data={'groupid': group_id, 'groupname': group_name})

    ret, _ = parse_resp(resp)
    return ret


def del_group(group_name=None, group_id=None):
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/deletegroup'
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name)
        if not group_id:
            raise Exception(f'could not find group:{group_name}')

    resp = requests.post(url, headers=HEADER,
                         data={'groupid': group_id})

    ret, _ = parse_resp(resp)
    return ret


def get_group_id(group_name):
    groups = get_groups()
    groups = [group for group in groups if group['name'] == group_name]
    if groups:
        return groups[0]['id']
    return None


def add_to_group(code, entity_type='stock', group_name=None, group_id=None):
    if not group_id:
        assert group_name is not None
        group_id = get_group_id(group_name)
        if not group_id:
            raise Exception(f'could not find group:{group_name}')
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/addstock'
    resp = requests.post(url, headers=HEADER,
                         data={'groupid': group_id, 'stockcode': to_eastmoney_code(code=code, entity_type=entity_type)})

    ret, _ = parse_resp(resp)
    return ret


def to_eastmoney_code(code, entity_type='stock'):
    if entity_type == 'stock':
        # 上海
        if code >= '333333':
            return f'1.{code}'
        else:
            return f'0.{code}'


__all__ = ['create_group', 'get_groups', 'rename_group', 'del_group', 'add_to_group', 'to_eastmoney_code']

if __name__ == '__main__':
    groups = get_groups()
    if len(groups) >= 9:
        del_group(group_id=groups[-2]['id'])

    create_group('tmp')
    add_to_group('000888', group_name='tmp')
    del_group('tmp')
