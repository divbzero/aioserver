"""A setuptools based setup module.
See:

https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os.path import abspath, dirname, join

here = abspath(dirname(__file__))

# Get the long description from the README file
with open(join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='aioserver',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.7.4',

    description='An async web framework for humans',
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url='https://github.com/divbzero/aioserver',

    # Author details
    author='Chris Lei',
    author_email='chris@divbzero.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Related frameworks
        'Framework :: AsyncIO',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',

        # Related topics
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
    ],

    # What does your project relate to?
    keywords='asyncio aiohttp async web framework forhumans simple HTTP server CORS',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['aioserver'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #  py_modules=['aioserver'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['aiohttp'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    #   extras_require={
    #       'dev': ['check-manifest'],
    #       'test': ['coverage'],
    #   },

    # If your project only runs on certain Python versions, setting the
    # python_requires argument to the appropriate PEP 440 version specifier
    # string will prevent pip from installing the project on other Python
    # versions.
    python_requires='>=3.5',

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    #   package_data={
    #       'sample': ['package_data.dat'],
    #   },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #   data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    #   entry_points={
    #       'console_scripts': [
    #           'sample=sample:main',
    #       ],
    #   },
)
