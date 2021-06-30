from pathlib import Path
from setuptools import setup

setup(
    name="autotyper",
    version="0.0.1",
    description="A tool for autoadding simple type annotations.",
    long_description=Path("README.md").read_text(),
    keywords="typing annotations",
    author="Jelle Zijlstra",
    author_email="jelle.zijlstra@gmail.com",
    url="https://github.com/JelleZijlstra/autotyper",
    project_urls={"Bug Tracker": "https://github.com/JelleZijlstra/autotyper/issues"},
    license="MIT",
    packages=["autotyper"],
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
