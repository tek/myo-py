from setuptools import setup, find_packages

version_parts = (1, 0, 2, 'a', 1)
version = '.'.join(map(str, version_parts))

setup(  # type: ignore
    name='myo',
    description='command and layout management for neovim',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/myo',
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*', 'test', 'test.*']),
    install_requires=[
        'ribosome==13.0.1a6',
        'chiasma~=0.1.0.a28',
        'psutil==5.3.1',
        'networkx==2.0',
        'lark-parser==0.6.5',
    ],
    tests_require=[
        'kallikrein~=0.22.a17',
    ],
)
