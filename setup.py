"""
This is the setup module for the reusable-workflows project.

Based on:

- https://packaging.python.org/distributing/
- https://github.com/pypa/sampleproject/blob/master/setup.py
- https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
"""

# Standard Python Libraries
from glob import glob
from os.path import basename, dirname, join, splitext
import re

# Third-Party Libraries
from setuptools import find_packages, setup


def readme():
    """Read in and return the contents of the project's README.md file."""
    with open("README.md", encoding="utf-8") as f:
        return f.read()


def cargo_version():
    """Manually extract version from Cargo.toml."""
    cargo_toml_path = join(dirname(__file__), "Cargo.toml")
    version_pattern = r'^version\s*=\s*"(.*?)"$'
    with open(cargo_toml_path, encoding="utf-8") as f:
        for line in f:
            match = re.match(version_pattern, line.strip())
            if match:
                return match.group(1)
    # Raise an exception if version is not found
    raise RuntimeError("Version not found in Cargo.toml")


setup(
    name="reusable-workflows",
    # Versions should comply with PEP440
    version=cargo_version(),
    description="reusable workflows for GitHub Actions",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/felddy",
    # The project's main homepage
    download_url="https://github.com/felddy/reusable-workflows",
    # Author details
    author="Mark Feldhousen",
    author_email="markf@geekpad.com",
    license="License :: OSI Approved :: MIT License",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.8",
    # What does your project relate to?
    keywords="workflows, github, actions, reusable, docker, pytest, pre-commit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    install_requires=[
        "semver == 3.0.2",
        "setuptools == 70.3.0",
        "wheel == 0.43.0",
    ],
    extras_require={
        "test": [
            "coverage == 6.5.0",
            "coveralls == 4.0.1",
            "docker == 7.1.0",
            "pre-commit == 3.7.1",
            "pytest == 8.2.2",
            "pytest-cov == 5.0.0",
            "pytest-lazy-fixture == 0.6.3",
        ]
    },
)
