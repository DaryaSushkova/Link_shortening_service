import uuid
import string


BASE62 = string.digits + string.ascii_letters


def encode_base62(num: int) -> str:
    """
    Алгоритм генерации base62-кода.
    """

    if num == 0:
        return BASE62[0]
    
    base62 = []
    while num > 0:
        num, rem = divmod(num, 62)
        base62.append(BASE62[rem])

    return ''.join(reversed(base62))


def generate_short_code_from_uuid(u: uuid.UUID = None, length: int = 10) -> str:
    """
    Генерирация base62-код из UUID.
    """
    
    u = u or uuid.uuid4()
    code = encode_base62(u.int)
    return code[:length]