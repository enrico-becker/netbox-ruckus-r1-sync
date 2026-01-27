from setuptools import setup, find_packages

setup(
    name="netbox-ruckus-r1-sync",
    version="0.1.0",
    description="RUCKUS Networks - RUCKUS ONE to Netbox Sync Plugin for NetBox",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Enrico Becker, RUCKUS Networks",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
    ],
    url="https://github.com/enrico-becker/netbox-ruckus-r1-sync/",
    license="Apache 2.0",
    keywords=["netbox-plugin"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
    ],
    project_urls={
        "Source": "https://github.com/enrico-becker/netbox-ruckus-r1-sync/",
    },
)

