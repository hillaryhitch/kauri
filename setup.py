from setuptools import setup, find_packages

setup(
    name="kazuri",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.15.0",
        "rich>=13.9.0",
        "boto3>=1.35.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
    ],
    entry_points={
        "console_scripts": [
            "kazuri=kazuri.cli:main",
        ],
    },
    author="Hillary Murefu",
    author_email="hillarywang2005@gmail.com",
    description="Kazuri - Your AI-powered development assistant using AWS Bedrock",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hillaryhitch/kazuri",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
)
