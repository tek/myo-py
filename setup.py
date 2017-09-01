from setuptools import setup, find_packages

version_parts = (0, 33, 0)
version = '.'.join(map(str, version_parts))

setup(
    name='myo',
    description='command and layout management for neovim',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/myo',
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*']),
    install_requires=[
        'ribosome==10.16.2',
        'libtmux',
        'psutil',
        'networkx',
    ],
    tests_require=[
        'kallikrein',
    ],
)
