class BaseException(Exception):
    def __init__(self, error_message: str):
        self.error = error_message


class SchemaParsingError(BaseException):
    pass


class SchemaFieldError(BaseException):
    pass


class UnknownTransmutator(BaseException):
    pass


class TransmutatorError(BaseException):
    pass
