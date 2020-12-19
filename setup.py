from setuptools import setup, find_packages

setup(
    name='django-wildewidgets',
    version="0.1.2",
    description='django-wildewidgets is a Django app to help make charts, tables, and UI widgets quickly and easily with libraries like Chartjs, Altair, and Datatables.',
    long_description=open('README.md', 'rt').read(),
    author="IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    url='https://github.com/caltechads/django-wildewidget',
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
)
