from setuptools import setup, find_packages

setup(
    name='django-wildewidgets',
    version="0.2.0",
    description='django-wildewidgets is a Django library designed to help you make charts, graphs, tables, and UI widgets quickly and easily with libraries like Chartjs, Altair, and Datatables.',
    long_description=open('README.md', 'rt').read(),
    long_description_content_type="text/markdown",
    author="IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    url='https://github.com/caltechads/django-wildewidget',
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
)
