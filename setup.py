# File: setup.py
from setuptools import setup, find_packages

setup(
    name="addis-bingo",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=3.0.0",
        "flask-sqlalchemy>=3.1.0",
        "aiogram>=3.0.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=1.0.0",
    ],
)