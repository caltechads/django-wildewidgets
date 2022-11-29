from setuptools import setup, find_packages

setup(
    name='django-wildewidgets',
    version="0.13.51",
    description='django-wildewidgets is a Django design library providing several tools for building full-featured, widget-based web applications with a standard, consistent design, based on Bootstrap.',
    long_description=open('README.md', 'rt').read(),
    long_description_content_type="text/markdown",
    author="IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    url='https://github.com/caltechads/django-wildewidget',
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
)
