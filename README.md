# CI for Python Packages
**Simple Python script to run CI for a Python package on different platforms**

Does running multiple CI configuration files annoy you? Do updates of 
`pip` and other core packages break your builds? Good! They did for me
as well, and maintaining multiple CI setups with different
configurations got very annoying.

That's why this repository contains a modified version of the `ci.py` I
had written for the `ttkthemes` package. By using environment variables
and custom hook files the behaviour can be adjusted for any Python 
package, or that's the plan anyway.

