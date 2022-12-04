import hashlib


def pwd_md5(key, val):
    '''

    :param key: 账户
    :param val: 密码
    :return:
    '''
    md5 = hashlib.md5()
    if not isinstance(key, str) or not isinstance(val, str):
        key = str(key)
        val = str(val)
    md5.update(key.title().encode('utf8'))
    md5.update(val.title().encode('utf8'))

    return md5.hexdigest()

