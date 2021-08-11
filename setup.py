import os
import setuptools
from packaging.version import Version

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

version_string = os.environ.get("MVG_RELEASE_VERSION", "")

if version_string:
    # Parse release version from env variable.
    # This will only happen if we are running as part of the pypi workflow
    # Will throw an error if version string is not valid
    version = Version(version_string)
else:
    # Allow for dev environment installation through pip install -e .
    version = Version("0.0.0.dev0")

setuptools.setup(
    name="va-mvg",
    version=str(version),
    author="Viking Analytics",
    author_email="info@vikinganalytics.se",
    description="MultiViz Analytics Engine library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vikinganalytics/mvg",
    packages=["mvg", "mvg/features"],
    license="LICENSE",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=required,
)
