"""
Factory for the different types of repositories.
"""

def create_repository(name, settings):
    from .memory import Repository

    return Repository(settings)
