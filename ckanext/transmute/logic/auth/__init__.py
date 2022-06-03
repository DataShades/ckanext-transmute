from . import get


def get_auth_functions():
    return {
        "tsm_transmute": get.transmute,
    }
