from setuptools import setup, find_packages

version_parts = (1, 0, 0, 'a', 3)
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
        'ribosome~=13.0.0a36',
        'chiasma~=0.1.0.a18',
        'psutil==5.3.1',
        'networkx==2.0',
    ],
    tests_require=[
        'kallikrein',
    ],
)
