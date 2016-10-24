from setuptools import setup, find_packages

version_parts = (0, 26, 0)
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
        'ribosome>=9.12.4',
        'amino>=8.9.0',
        'libtmux',
        'psutil',
        'networkx',
    ]
)
