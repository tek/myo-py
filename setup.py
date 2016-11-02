from setuptools import setup, find_packages

version_parts = (0, 27, 10)
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
        'ribosome>=9.12.9',
        'amino>=8.9.2',
        'libtmux',
        'psutil',
        'networkx',
    ]
)
