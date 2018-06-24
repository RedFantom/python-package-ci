"""
Author: RedFantom
License: GNU GPLv3
Copyright (c) 2017-2018 RedFantom
"""
import os

SCRIPT = 'https://raw.githubusercontent.com/RedFantom/python-package-ci/master/ci.py'


TRAVIS_CI_BEFORE = [
    # Initializes virtual screen
    "  - if [[ \"$TRAVIS_OS_NAME\" == \"linux\" ]]; then",
    "      export DISPLAY=:99.0;",
    "      sh -e /etc/init.d/xvfb start;",
    "      sleep 3;",
    # Installs Python on macOS
    "    else",
    "      brew upgrade python wget || echo \"Installed Python and wget\";",
    "    fi;",
    "  - wget {}".format(SCRIPT),
    "  - $PYTHON -m pip install configparser -U",
]

TRAVIS_SCRIPT = [
    "script:",
    "  - $PYTHON ci.py",
]

TRAVIS_OSX_MATRIX_ELEM = [
    "  - os: osx",
    "language: generic",
    "env: PYTHON=python3 NUMBER='36' OS='darwin'",
]


APPVEYOR_BEFORE = [
    "before_test:",
    "  - ps: Start-FileDownload '{}'".format(SCRIPT),
    "  - %PYTHON%\\python.exe -m pip install configparser -U"
]


APPVEYOR_SCRIPT = [
    "test_script:",
    "  - \"%PYTHON%\\python.exe ci.py\""
]


def askyesno(prompt, default="n"):
    result = input("{} (y/n) [n]: ".format(prompt))
    result = default if result == "" else result
    return result == "y"


def asklist(prompt):
    result = input("{}: ".format(prompt))
    elements = result.split(",")
    if len(elements) == 0:
        return asklist(prompt)
    return elements


def askoption(prompt, options, default):
    result = input("{} ({}) [{}]: ".format(prompt, ",".join(options), default))
    result = default if result.strip() == "" else result
    if result not in options:
        return askoption(prompt, options, default)
    return result


def askdist():
    return askoption("What distributions should be created?", ("sdist", "bdist", "both"), "both")


def askversions():
    return asklist("Enter Python versions (separated by a comma)")


def travis_build_matrix_elem(version, dist):
    """Build an element for the platform matrix"""
    elem = ["  - os: linux", "    python: '{}'".format(version)]
    env = "    env: PYTHON=python NUMBER={} OS=\"linux\"".format(version.replace(".", ""))
    if dist == "sdist":  # Source distribution only
        env += " SDIST=\"true\""
    elem.append(env)
    return elem


def travis_build_matrix(versions, dist, macos):
    """
    Build a Travis-CI build matrix based on the given parameters
    :param versions: list of Python versions ('3.4', '2.7', etc)
    :param dist: Distribution type to create (sdist, bdist, both)
    :param macos: Whether to build wheels on macOS (python 3.6 only)
    """
    matrix = ["matrix:", "  include:"]
    for version in versions:
        matrix.extend(travis_build_matrix_elem(version, dist))
    if dist == "both":
        # sdist is built on the latest Python to test on
        version = str(max(map(float, versions)))
        matrix.extend(travis_build_matrix_elem(version, "sdist"))
    if macos is True:
        matrix.extend(TRAVIS_OSX_MATRIX_ELEM)
    return matrix


def appveyor_build_matrix_elem(version, dist, _64bit):
    """Build a single AppVeyor build matrix element"""
    path = "C:\\PYTHON{}".format(version.replace(".", ""))
    if _64bit is True:
        path += "-x64"
    elem = ["    - PYTHON: \"{}\"".format(path)]
    if dist == "sdist":
        elem.append("      SDIST: \"true\"")
    return elem


def appveyor_build_matrix(versions, dist, _64bit):
    """
    Build an AppVeyor YAML build matrix from the parameters
    :param versions: list of python versions
    :param dist: distribution type to create
    :return: YAML file elements
    """
    matrix = ["environment:", "  matrix:"]
    for version in versions:
        matrix.extend(appveyor_build_matrix_elem(version, dist, False))
        if _64bit is True:
            matrix.extend(appveyor_build_matrix_elem(version, dist, True))
    if dist == "both":
        version = str(max(map(float, versions)))
        matrix.extend(appveyor_build_matrix_elem(version, "sdist", _64bit))
    return matrix


def save_yaml(filename, file):
    if os.path.exists(filename):
        overwrite = askyesno("{} exists. Overwrite?".format(filename))
        if not overwrite:
            exit(0)
        os.remove(filename)
    with open(filename, "w") as fo:
        fo.write("\n".join(file))


if __name__ == '__main__':
    print("** CI YAML File Generator **\n")

    if askyesno("Set-up a Travis-CI YAML file?"):
        """
        Build a Travis-CI YAML file from the instructions
        
        Options:
        - sudo required
        - Ubuntu dist
        - python versions
        - sdist, bdist or both
        - operating systems 
        """
        # TODO: Artifact deployment
        file = ["language: python"]
        # sudo
        if askyesno("Do you need package based dependencies?"):
            file.append("sudo: required")
        # dist
        if askyesno("Do you need a specific Ubuntu version?"):
            file.append("dist: {}".format(input("Version: ")))
        # python versions
        versions = askversions()
        # dist types
        dist = askdist()
        # macOS
        macos = askyesno("Do you want wheel building on macOS?")
        # Build the platform matrix
        file.extend(travis_build_matrix(versions, dist, macos))
        # Default elements
        file.extend(TRAVIS_SCRIPT)
        # Save the file
        save_yaml(".travis.yml", file)
        print("Successfully created Travis YAML file.\n\n")

    if askyesno("Set-up an AppVeyor YAML file?"):
        """
        Build an AppVeyor YAML file
        
        Options:
        - Python versions
        - 64-bit required
        """
        versions = askversions()
        dist = askdist()
        _64bit = askyesno("Do you want to test on 64-bit versions?")
        file = appveyor_build_matrix(versions, dist, _64bit)
        file.extend(APPVEYOR_BEFORE + APPVEYOR_SCRIPT)
        save_yaml(".appveyor.yml", file)
        print("Successfully created AppVeyor YAML file.\n\n")
