"""Setup script for UberFile."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="uberfile",
    version="1.0.0",
    author="Shutdown & en1ma",
    author_email="",
    description="A tool for generating file transfer commands and serving files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ShutdownRepo/uberfile",
    packages=find_packages(include=['uberfile', 'uberfile.*']),
    package_data={
        'uberfile': ['py.typed'],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "uberfile=uberfile.__main__:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/ShutdownRepo/uberfile/issues",
        "Source": "https://github.com/ShutdownRepo/uberfile",
    },
    keywords="file transfer, command generation, server, security, networking",
)
