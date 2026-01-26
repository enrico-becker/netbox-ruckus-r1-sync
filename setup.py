from setuptools import setup, find_packages

setup(
    name="netbox-ruckus-r1-sync",
    version="0.1.0",
    description="RUCKUS Networks - RUCKUS ONE to Netbox Sync Plugin for NetBox",
    author="Enrico Becker, RUCKUS Networks",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
    ]
)
