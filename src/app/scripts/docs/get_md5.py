import hashlib


def get_md5(bt):
    """
    :param bt: bytes
    :return:
    """

    md5f = hashlib.md5()
    md5f.update(bt)
    file_md5 = md5f.hexdigest()
    return file_md5
