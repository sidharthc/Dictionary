from setuptools import setup, find_packages

setup(
    name="hipappear",
    version="0.0.1",
    packages=find_packages('hipappear'),
    package_dir={'': 'hipappear'},
    install_requires=['setuptools', 'requests'],
)
