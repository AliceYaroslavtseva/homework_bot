class SendMessageError(Exception):
    """.
    Исключение в случае не отравки сообщения.
    """
    pass


class APIResponsError(Exception):
    """.
    Исключение в случае, если вызов API
    возвращает статус отличный от 200.
    """
    pass


class ParameterNotTypeError(Exception):
    """.
    Исключение в случае, если параметр
    не приведен к типу данных Python.
    """
    pass


class  NoKeyError(Exception):
    """.
    В словаре нет ключа.
    """
    pass
