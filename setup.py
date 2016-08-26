from setuptools import setup, find_packages

setup(
    name='myo',
    description='command and layout management for neovim',
    version='0.0.2',
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/myo',
    packages=find_packages(exclude=['unit', 'unit.*']),
    install_requires=[
        'ribosome>=8.0.0',
        'libtmux',
        'psutil',
        'networkx',
    ]
)
