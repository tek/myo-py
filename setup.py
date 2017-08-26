from setuptools import setup, find_packages

version_parts = (0, 32, 7)
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
        'ribosome==10.13.0',
        'libtmux',
        'psutil',
        'networkx',
    ],
    tests_require=[
        'kallikrein',
    ],
)
