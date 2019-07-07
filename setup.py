from setuptools import setup, find_packages

setup(
    name='uatu',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        uatu=uatu.cli:cli
    ''',
)