from setuptools import setup

from packageinfo import NAME, VERSION

# Read description
with open("README.md", "r") as readme:
    README_TEXT = readme.read()

# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author="Materials Data Science and Informatics Team at Fraunhofer IWM",
    description="Dataverse repository query",
    keywords="dataverse repository, Fraunhofer IWM",
    long_description=README_TEXT,
    install_requires=[
        "Flask",
        "requests_oauthlib",
        "requests",
        "rdflib >= 6.0.2, < 7.0.0",
        "jsonpath-ng",
        "pycountry",  # For handling ISO 639-1 and ISO 639-2 language codes.
    ],
)
