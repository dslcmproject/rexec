from setuptools import setup


setup(
    name='rexec',
    version='0.0.1',
    description='Run Remote Executables',
    license="MIT",
    author='Marco De Paoli',
    author_email='depaolim@gmail.com',
    url="https://github.com/dslcmproject/rexec",
    packages=['rexec'],
    install_requires=[],  # external packages as dependencies
    scripts=['rexec_install.py']
)
