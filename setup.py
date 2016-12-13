from setuptools import setup, find_packages

version_parts = (0, 29, 1)
version = '.'.join(map(str, version_parts))

setup(
    name='myo',
    description='command and layout management for neovim',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/myo',
    packages=find_packages(exclude=['unit', 'unit.*']),
    install_requires=[
        'ribosome>=9.12.13',
        'amino>=8.9.10',
        'libtmux',
        'psutil',
        'networkx',
    ]
)
