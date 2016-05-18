from setuptools import setup, find_packages
import sys

if sys.version_info[0] < 3:
    import __builtin__ as builtins
else:
    import builtins

# This is a bit (!) hackish: we are setting a global variable so that the main
# graphql __init__ can detect if it is being loaded by the setup routine, to
# avoid attempting to load components that aren't built yet:
# the numpy distutils extensions that are used by scikit-learn to recursively
# build the compiled extensions in sub-packages is based on the Python import
# machinery.
builtins.__GRAPHQL_SETUP__ = True

version = __import__('graphql').get_version()

setup(
    name='graphql-core',
    version=version,
    description='GraphQL implementation for Python',
    url='https://github.com/graphql-python/graphql-core',
    download_url='https://github.com/graphql-python/graphql-core/releases',
    author='Syrus Akbary, Jake Heinz, Taeho Kim',
    author_email='Syrus Akbary <me@syrusakbary.com>, Jake Heinz <me@jh.gg>, Taeho Kim <dittos@gmail.com>',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
    ],

    keywords='api graphql protocol rest',
    packages=find_packages(exclude=['tests', 'tests_py35']),
    install_requires=[
        'six>=1.10.0',
        'promise>=0.4.0'
    ],
    tests_require=[
        'pytest>=2.7.3',
        'gevent==1.1rc1',
        'six>=1.10.0',
        'pytest-mock'
    ],
    extras_require={
        'gevent': [
            'gevent==1.1rc1'
        ]
    }
)
