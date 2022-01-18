import io
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

here = abspath(dirname(__file__))

with io.open(join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with io.open(join(here, 'requirements.txt'), encoding='utf-8') as f:
    requires = f.read().splitlines()

setup(
    name='moler',  # Required
    version='2.0.0',  # Required
    description='Moler is library to help in building automated tests',  # Required
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional (see note above)
    url='https://github.com/nokia/moler',  # Optional
    author='Nokia',  # Optional
    license='BSD 3-Clause',
    classifiers=[  # Optional
        'Development Status :: 3 - Alpha',

        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: BSD License',

        'Operating System :: POSIX',
        'Operating System :: Unix',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Topic :: Software Development',
        'Topic :: Software Development :: Testing',
        'Topic :: System :: Networking'
    ],

    keywords='testing development',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=['docs', 'examples', 'images', 'test']),  # Required

    package_data={'moler': ['config/bash_config']},

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=requires,  # Optional

    project_urls={  # Optional
        'Bug Reports': 'https://github.com/nokia/moler/issues',
        'Source': 'https://github.com/nokia/moler',
    },
)
