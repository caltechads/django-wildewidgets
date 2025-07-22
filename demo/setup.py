from setuptools import find_packages, setup  # noqa: INP001

setup(
    name="demo",
    version="1.1.7",
    description="",
    author="Caltech IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests", "htmlcov"]
    ),
)
