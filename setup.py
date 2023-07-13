from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='django-wildewidgets',
    version="0.16.11",
    packages=find_packages(exclude=['bin']),
    include_package_data=True,
    description='django-wildewidgets is a Django design library providing several tools for '
                'building full-featured, widget-based web applications with a standard, '
                'consistent design, based on Bootstrap.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'django-crispy-forms',
        'crispy-bootstrap5',
    ],
    author="Caltech IMSS ADS",
    author_email="imss-ads-staff@caltech.edu",
    url='https://github.com/caltechads/django-wildewidgets',
    keywords=['design', 'widget', 'django'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Topic :: Software Development :: User Interfaces",
    ],
)
