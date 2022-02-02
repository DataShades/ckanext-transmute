import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.transmute.logic.action import get_actions
from ckanext.transmute.logic.auth import get_auth_functions
from ckanext.transmute.cli import get_commands


class TransmutePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IClick)
    p.implements(p.IAuthFunctions)

    # IConfigurer
    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic',
            'transmute')

    # IActions
    def get_actions(self):
        """Registers a list of extension specific actions
        """
        return get_actions()
    
    # IClick
    def get_commands(self):
        """Registers a list of extension specific CLI commands
        """
        return get_commands()

    # IAuthFunctions
    def get_auth_functions(self):
        """Registers a list of extension specific auth function
        """
        return get_auth_functions()