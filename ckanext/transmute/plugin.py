import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.transmute.actions import get_actions


class TransmutePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IActions)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic',
            'transmute')

    # IActions

    def get_actions(self):
        return get_actions()
