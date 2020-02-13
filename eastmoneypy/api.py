import requests

from eastmoneypy import my_env


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


def list_groups():
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/group'

    resp = requests.get(url, headers=HEADER)

    groups = resp.json()['result']['groups']

    return groups


def add_to_group(code, entity_type='stock', group_id=None, group_name=None):
    if not group_id:
        assert group_name is not None
        groups = list_groups()
        groups = [group for group in groups if group['name'] == group_name]
        if groups:
            group_id = groups[0]['id']
        else:
            raise Exception(f'could not find group:{group_name}')
    url = 'http://quote.eastmoney.com/zixuan/api/zxg/addstock'
    resp = requests.post(url, headers=HEADER,
                         data={'groupid': group_id, 'stockcode': to_eastmoney_code(code=code, entity_type=entity_type)})

    print(resp.json())


def to_eastmoney_code(code, entity_type='stock'):
    if entity_type == 'stock':
        # 上海
        if code >= '333333':
            return f'1.{code}'
        else:
            return f'0.{code}'


if __name__ == '__main__':
    list_groups()
    add_to_group('000878', group_name='ing')

__all__ = ['list_groups', 'add_to_group']
