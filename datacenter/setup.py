from setuptools import setup

setup(
    name='decentralized-ml',
    version='0.1.0',
    author="DataAgora",
    author_email="georgymarrero@berkeley.edu",
    packages=[
        'core',
        'custom',
        'data',
        'models',
    ],
    entry_points={
        'console_scripts': [
            'dml = core.__main__:main'
        ]
    },
)
