from setuptools import setup, find_packages

setup(
    name="capyface-commons",
    version="0.4.0",
    packages=find_packages(),
    package_data={
        '': ['*.proto'],
        'capyface_commons.generated': ['*_pb2.py', '*_pb2_grpc.py'],
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.25.0",
        "grpcio>=1.71.0",
        "protobuf<6.0dev,>=5.26.1",
        "redis>=5.2.0",
    ],
    author="CapyFace Team",
    author_email="sang080304@gmail.com",
    description="Shared utilities for CapyFace microservices",
    url="https://github.com/SangTin/capyface-commons",
)