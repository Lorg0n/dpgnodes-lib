from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dpgnodes",
    version="0.1",
    author="Lorg0n",
    author_email="lorgon.kv@gmail.com",
    description="The library adds a more convenient interface for interacting with the node editor in the dearpygui library. By adding it is possible to create programmes from the available nodes.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "dearpygui",
    ]
)