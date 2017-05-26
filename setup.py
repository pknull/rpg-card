try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'RPG Card Picker',
    'author': 'Louis Grenzebach',
    'url': 'https://github.com/pknull/rpg-card',
    'author_email': 'louis.grenzebach@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'name': 'card_picker'
}

setup(**config)

