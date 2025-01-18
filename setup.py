from setuptools import find_packages, setup

setup(
    name="masterzdran-azure-tablestorge-logging",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["azure-data-tables>=12.4.0", "azure-core>=1.26.0"],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
        ],
    },
    python_requires=">=3.8",
    author="Nuno Cancelo",
    author_email="nuno.cancelo@gmail.com",
    description="A professional logging module using Azure Table Storage",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/masterzdran/masterzdran-azure-tablestorge-logging",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
