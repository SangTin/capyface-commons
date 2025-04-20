from setuptools import setup, find_packages

setup(
    name="capyface-commons",
    version="0.2.1",
    packages=find_packages(),
    package_data={
        '': ['*.proto'],
        'capyface_commons.generated': ['*_pb2.py', '*_pb2_grpc.py'],
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "grpcio>=1.50.0",
        "protobuf>=4.25.0",
        "redis>=4.3.0",
    ],
    author="CapyFace Team",
    author_email="sang080304@gmail.com",
    description="Shared utilities for CapyFace microservices",
    url="https://github.com/SangTin/capyface-commons",
)