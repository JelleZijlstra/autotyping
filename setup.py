from pathlib import Path
from setuptools import setup

setup(
    name="autotyping",
    version="22.9.0",
    description="A tool for autoadding simple type annotations.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    keywords="typing annotations",
    author="Jelle Zijlstra",
    author_email="jelle.zijlstra@gmail.com",
    url="https://github.com/JelleZijlstra/autotyping",
    project_urls={"Bug Tracker": "https://github.com/JelleZijlstra/autotyping/issues"},
    license="MIT",
    packages=["autotyping"],
    install_requires=["libcst"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development",
    ],
    python_requires=">=3.6",
)
