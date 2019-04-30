import json

from setuptools import setup, find_packages


def load_requirements(path="./Pipfile.lock", default=True):
    with open(path, "rt") as f:
        rmt_obj = json.loads(f.read())
    rmt_obj = rmt_obj["default"] if default else rmt_obj["develop"]
    return rmt_obj.keys()


def load_long_description(path="./README.md"):
    with open(path, "rt") as f:
        return f.read()


def get_package_info(lines, identy):
    return list(filter(lambda s: identy in s, lines))[0].split('=', 1)[-1].strip(' "\n')


with open('./freesia/__init__.py', encoding='utf8') as f:
    lines = f.readlines()
    AUTHOR = get_package_info(lines, "__author__")
    VERSION = get_package_info(lines, "__version__")

setup(
    name="async_freesia",
    version=VERSION,
    author=AUTHOR,
    keywords="freesia, framework, backend",
    description="A concise and lightweight web framework.✨",
    long_description=load_long_description(),
    packages=find_packages(),
    install_requires=load_requirements(),
    include_package_data=True,
    test_suite="tests",
    license="MIT",
    url="https://github.com/AuraiProject/freesia",
)
