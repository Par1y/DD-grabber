from setuptools import setup, find_packages

setup(
    name='worker',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    entry_points={'scrapy': ['settings = worker.settings']},
)
