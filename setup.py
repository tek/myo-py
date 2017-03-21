from setuptools import setup, find_packages

version_parts = (0, 30, 1)
version = '.'.join(map(str, version_parts))

setup(
    name='myo',
    description='command and layout management for neovim',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/myo',
    packages=find_packages(exclude=['unit', 'unit.*', 'integration',
                                    'integration.*']),
    install_requires=[
        'ribosome>=10.1.0',
        'amino>=9.5.7',
        'libtmux',
        'psutil',
        'networkx',
    ]
)
