class TransmuteBaseException(Exception):
    def __init__(self, error_message: str):
        self.error = error_message


class SchemaParsingError(TransmuteBaseException):
    pass


class SchemaFieldError(TransmuteBaseException):
    pass


class UnknownTransmutator(TransmuteBaseException):
    pass


class TransmutatorError(TransmuteBaseException):
    pass
