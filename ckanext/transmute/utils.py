import logging

import ckan.plugins as p
from ckan.logic import _import_module_functions

from ckanext.transmute.exception import UnknownTransmutator
from ckanext.transmute.interfaces import ITransmute


_transmutator_cache = {}
log = logging.getLogger(__name__)


def get_transmutator(transmutator: str):
    if not _transmutator_cache:
        for plugin in reversed(list(p.PluginImplementations(ITransmute))):
            for name, fn in plugin.get_transmutators().items():
                log.debug(f'Transmutator function {name} from plugin {plugin.name} was inserted')
                _transmutator_cache[name] = fn

    try:
        return _transmutator_cache[transmutator]
    except KeyError:
        raise UnknownTransmutator(f'Transmutator {transmutator} does not exist')