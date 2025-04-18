from setuptools import setup, find_packages

setup(
    name="capyface-commons",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    author="CapyFace Team",
    author_email="sang080304@gmail.com",
    description="Shared utilities for CapyFace microservices",
    url="https://github.com/SangTin/capyface-commons",
)