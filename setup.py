import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FinanceDatabase",
    packages=["FinanceDatabase"],
    version="0.1.9",
    license="MIT",
    description="This is a database of 300.000+ symbols containing Equities, ETFs, Funds, Indices, Futures, "
                "Options, Currencies, Cryptocurrencies and Money Markets.",
    author="JerBouma",
    author_email="jer.bouma@gmail.com",
    url="https://github.com/JerBouma/FinanceDatabase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["finance", "database", "financials"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3"
    ],
)