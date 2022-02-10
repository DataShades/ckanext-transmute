import ckan.plugins.toolkit as tk


@tk.auth_allow_anonymous_access
def transmute(context, data_dict):
    return {"success": True}
