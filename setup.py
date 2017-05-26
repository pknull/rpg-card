try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'name': 'card_picker',
    'version': '0.1',
    'description': 'Card dealing system for use in RPG bots',
    'author': 'Louis Grenzebach',
    'author_email': 'louis.grenzebach@gmail.com',
    'url': 'https://github.com/pknull/rpg-card',
    'packages': [
        'card_picker'
    ],
    'install_requires': ['nose']
}

setup(**config)

