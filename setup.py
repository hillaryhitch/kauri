from setuptools import setup, find_packages

setup(
    name="kazuri",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "boto3",
        "python-dotenv"
    ],
    entry_points={
        'console_scripts': [
            'kazuri=kazuri.cli:main',
        ],
    },
)
