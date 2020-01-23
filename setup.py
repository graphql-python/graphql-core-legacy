from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys
import ast
import re

_version_re = re.compile(r"VERSION\s+=\s+(.*)")

with open("graphql/__init__.py", "rb") as f:
    version = ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1))

path_copy = sys.path[:]

sys.path.append("graphql")
try:
    from pyutils.version import get_version

    version = get_version(version)
except Exception:
    version = ".".join([str(v) for v in version])

sys.path[:] = path_copy

install_requires = ["six>=1.10.0", "promise>=2.3,<3", "rx>=1.6,<2"]

tests_requires = [
    "pytest==4.6.9",
    "pytest-django==3.8.0",
    "pytest-cov==2.8.1",
    "coveralls==1.10.0",
    "gevent==1.4.0",
    "six>=1.10.0",
    "pytest-benchmark==3.2.3",
    "pytest-mock==2.0.0",
]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ["graphql", "-vrsx"]
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="graphql-core",
    version=version,
    description="GraphQL implementation for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/graphql-python/graphql-core",
    download_url="https://github.com/graphql-python/graphql-core/releases",
    author="Syrus Akbary, Jake Heinz, Taeho Kim",
    author_email="me@syrusakbary.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: MIT License",
        "Topic :: Database :: Front-Ends",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="api graphql protocol rest",
    packages=find_packages(exclude=["tests", "tests_py35", "tests.*", "tests_py35.*"]),
    install_requires=install_requires,
    tests_require=tests_requires,
    cmdclass={"test": PyTest},
    extras_require={"gevent": ["gevent>=1.1"], "test": tests_requires},
    package_data={"graphql": ["py.typed"]},
)
