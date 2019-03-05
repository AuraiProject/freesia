import json
from setuptools import setup, find_packages

from freesia import AUTHOR, VERSION


def load_requirements(path="./Pipfile.lock", default=True):
    with open(path, "rt") as f:
        rmt_obj = json.loads(f.read())
    rmt_obj = rmt_obj["default"] if default else rmt_obj["develop"]
    rmt_list = []
    for key, value in rmt_obj.items():
        rmt_list.append(
            key + value["version"]
        )
    return rmt_list


def load_long_description(path="./README.rst"):
    with open(path, "rt") as f:
        return f.read()


setup(
    name="freesia",
    version=VERSION,
    author=AUTHOR,
    keywords="freesia, framework, backend",
    description="A concise and lightweight web framework.✨",
    long_description=load_long_description(),
    packages=find_packages(where='freesia'),
    install_requires=load_requirements(),
    include_package_data=True,
    test_suite="tests",
    license="MIT",
    url="https://github.com/AuraiProject/freesia",
)
