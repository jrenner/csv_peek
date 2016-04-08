"""Curses app for viewing CSV files."""


from setuptools import setup


setup(
    name='peek',
    version='0.2',
    description='Curses app for viewing CSV files.',
    long_description='Curses app for viewing CSV files.',
    url='https://github.umn.edu/mpc/peek',
    author='Jon Renner',
    author_email='jrenner@umn.edu',
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='data viewer console curses',
    packages=['peek'],
    entry_points={
        'console_scripts': [
             'peek=peek:main',
        ],
    },
)
