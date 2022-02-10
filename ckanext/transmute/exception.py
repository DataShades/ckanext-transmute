from ckan.logic import ValidationError


class BaseException(Exception):
    def __init__(self, error_message: str):
        self.error = error_message


class ValidationError(ValidationError):
    pass


class SchemaParsingError(BaseException):
    pass


class SchemaFieldError(BaseException):
    pass
