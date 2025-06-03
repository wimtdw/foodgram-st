import string


BASE62_ALPHABET = string.digits + string.ascii_letters
BASE62_LENGTH = len(BASE62_ALPHABET)


def encode_id_to_base62(pk: int) -> str:
    """Преобразует ID в строку base62"""
    if pk == 0:
        return BASE62_ALPHABET[0]

    result = []
    num = pk
    while num:
        num, rem = divmod(num, BASE62_LENGTH)
        result.append(BASE62_ALPHABET[rem])
    return "".join(result[::-1])


def decode_base62_to_id(short_code: str) -> int:
    """Преобразует строку base62 обратно в ID"""
    num = 0
    for char in short_code:
        num = num * BASE62_LENGTH + BASE62_ALPHABET.index(char)
    return num
