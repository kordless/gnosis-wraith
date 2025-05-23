from setuptools import setup, find_packages

setup(
    name='gnosis_wraith',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'anthropic',
        'python-dotenv',
        'pytest',
    ],
)
