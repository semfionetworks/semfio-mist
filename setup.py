import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="semfio-mist",
    version="0.1.0",
    description="Set of functions to interact with the Mist Juniper Cloud",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/semfionetworks/semfio-mist.git",
    author="François Vergès",
    author_email="fverges@semfionetworks.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["semfio_mist"],
    include_package_data=True,
    install_requires=["requests"]
)
