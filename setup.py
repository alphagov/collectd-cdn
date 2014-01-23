import os
from setuptools import setup, find_packages

from collectd_cdn import __version__

HERE = os.path.dirname(__file__)
try:
    long_description = open(os.path.join(HERE, 'README.rst')).read()
except:
    long_description = None

setup(
    name='collectd-cdn',
    version=__version__,
    packages=find_packages(exclude=['test*']),

    # metadata for upload to PyPI
    author='Dan Carley',
    author_email='dan.carley@gmail.com',
    maintainer='Government Digital Service',
    url='https://github.com/gds-operations/collectd-cdn',

    description='CDN stats plugin for collectd',
    long_description=long_description,
    license='MIT',
    keywords='collectd cdn stats fastly'
)
