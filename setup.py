try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="card_picker",
    version="0.2",
    description="Card dealing system for use in RPG bots",
    author="Louis Grenzebach",
    author_email="louis.grenzebach@gmail.com",
    url="https://github.com/pknull/rpg-card",
    packages=["card_picker"],
    include_package_data=True,
    zip_safe=False,
    keywords="rpg card",
)
