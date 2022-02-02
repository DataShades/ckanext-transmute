import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.transmute.actions import get_actions
from ckanext.transmute.cli import get_commands


class TransmutePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)
    p.implements(p.IClick)

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
