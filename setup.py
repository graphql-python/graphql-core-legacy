import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='graphql-py',
    version='0.1a0',

    description='GraphQL implementation for Python',

    url='https://github.com/dittos/graphql-py',

    author='Taeho Kim',
    author_email='dittos' '@' 'gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2',
    ],

    keywords='api graphql protocol rest',

    packages=find_packages(exclude=['tests']),

    install_requires=[],
    tests_require=['pytest>=2.7.2'],
    extras_require={
        'django': [],
    },

    cmdclass={'test': PyTest},
)
