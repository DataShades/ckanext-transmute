import click


def get_commands():
    return [transmute]


@click.group()
def transmute():
    """Basic CLI commands group for ckanext-transmute
    """
    pass
