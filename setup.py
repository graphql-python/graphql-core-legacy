from re import search
from setuptools import setup, find_packages

with open("graphql/__init__.py") as init_file:
    version = search('__version__ = "(.*)"', init_file.read()).group(1)

with open("README.md") as readme_file:
    readme = readme_file.read()

install_requires = ["promise>=2.2.1", "rx>=1.6.1"]


tests_requires = [
    "pytest",
    "pytest-cov",
    "pytest-describe",
    "flake8",
    "mypy",
    "tox",
    "python-coveralls",
]

setup(
    name="GraphQL-core",
    version=version,
    description="GraphQL-core is a Python port of GraphQL.js,"
    " the JavaScript reference implementation for GraphQL.",
    long_description=readme,
    long_description_content_type="text/markdown",
    keywords="graphql",
    url="https://github.com/graphql-python/graphql-core",
    author="Syrus Akbary",
    author_email="me@syrusakbary.com",
    license="MIT license",
    # PEP-561: https://www.python.org/dev/peps/pep-0561/
    # package_data={"graphql": ["py.typed"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=install_requires,
    python_requires=">=3.6",
    test_suite="tests",
    tests_require=tests_requires,
    packages=find_packages(include=["graphql"]),
    include_package_data=True,
    zip_safe=False,
    extras_require={"test": tests_requires},
)

