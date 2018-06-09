# CI for Python Packages
**Simple Python script to run CI for a Python package on different platforms**

Does running multiple CI configuration files annoy you? Do updates of 
`pip` and other core packages break your builds? Good! They did for me
as well, and maintaining multiple CI setups with different
configurations got very annoying.

That's why this repository contains a modified version of the `ci.py` I
had written for the `ttkthemes` package. By using a simple ini
configuration file that is read with a `ConfigParser`, custom
dependencies can be installed (like system packages on Linux).

While technically all of this is possible by using YAML configuration
files, as used by AppVeyor and Travis-CI, I have found it to be 
tedious to keep up to date with changes in both Travis-CI and various
dependencies (like the `pip==10.0.0` update) for all of my repositories.

## Usage
The `ci.py` should be run by the test system. `ci.py` will automatically
install dependencies defined in a `requirements.txt` in the root of 
your repository, as well as any additional dependencies configured in
the `ci.ini`, or `.ci.ini`, file.

You can define your own platform matrix, but you can also build one with
the help of the `platform.py` script. This will generate YAML-files for
AppVeyor and Travis-CI alike.
