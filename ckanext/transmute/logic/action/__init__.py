from . import get


def get_actions():
    return {
        'tsm_transmute': get.transmute,
        'tsm_validate': get.validate,
    }
