from setuptools import setup, find_packages

setup(
    name='graphql-core',
    version='0.1a4',
    description='GraphQL implementation for Python',

    url='https://github.com/graphql-python/graphql-core',

    author='GraphQL Python',
    author_email='me' '@' 'jh.gg',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    keywords='api graphql protocol rest',

    packages=find_packages(exclude=['tests', 'tests_py35']),

    install_requires=['six>=1.10.0'],
    tests_require=['pytest>=2.7.3', 'gevent==1.1b5', 'six>=1.10.0'],
    extras_require={
        'gevent': [
            'gevent==1.1b5'
        ]
    }
)
