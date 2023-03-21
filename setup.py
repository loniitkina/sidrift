import setuptools
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sidrift",
    version="0.1.0",
    author="Polona Itkin",
    author_email="polona.itkin@uit.no",
    description="Sea ice deformation and backtrajectories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loniitkina/sidrift",
    packages=setuptools.find_packages(include=["sidrift"]),
    scripts=["bin/sidtrack"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        # list any dependencies here
    ],
)
