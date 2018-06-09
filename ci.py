"""
Author: RedFantom
License: GNU GPLv3
Copyright (c) 2017-2018 RedFantom
"""
from configparser import ConfigParser
import logging
import os
from shutil import rmtree
import sys

DEPENDENCIES = ["pillow"]
REQUIREMENTS = ["codecov", "coverage", "nose", "setuptools", "pip", "wheel", "semantic_version"]
PACKAGES = "python-tk python3-tk libtk-img"

SDIST = os.environ.get("SDIST", "false") == "true"

TO_DELETE = ["ttkthemes", "tkimg"]


def run_command(command):
    """
    :param command: command to run on os.system
    :return: exit code
    """
    print("Running system command: ", command)
    return_info = os.system(command)
    if sys.platform == "win32":
        return return_info
    else:
        return os.WEXITSTATUS(return_info)


class CI(object):
    """
    Manages a CI instance on AppVeyor or Travis-CI for a Python project

    Configuration of this class should happen in the `ci.ini`, or
    alternatively `.ci.ini`, file. This class will automatically detect
    the platform that is being run on and install the packages
    appropriately.
    """

    TRAVIS_CI = "travis"
    APPVEYOR = "appveyor"

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"

    CONFIG = ["ci.ini", ".ci.ini"]

    def __init__(self, platform=None):
        """
        :param platform: Optional platform override
        """
        self.logger = self.setup_logger()
        self.platform = platform if platform is not None else self.get_platform()
        self.os = self.get_os()
        self.config = ConfigParser()
        self.read_config()

    def build_wheel(self):
        """Build a wheel from a package"""
        pass

    def read_config(self):
        """Read the configuration file from disk"""
        path = self.get_config_path()
        if path is None:
            raise FileNotFoundError("Configuration file could not be found")
        self.config.read_file(path)

    @staticmethod
    def get_built_package_exists():
        """Return whether the wheel or sdist has been built and exists"""
        return len([file for file in os.listdir("dist") if file.endswith((".whl", ".tar.gz"))]) != 0

    @staticmethod
    def pip_install(pkgs: list):
        """Install a list of packages with pip"""

        # Import pip
        from pip import __version__ as pip_version
        if Version(pip_version) >= Version("10.0.0"):
            import pip._internal as pip
        else:
            import pip

        # Install/upgrade the specified packages
        command = ["install", "-U"] + pkgs
        pip.main(command)

    @staticmethod
    def get_config_path():
        """Return the absolute path to the config file if it exists"""
        for file in CI.CONFIG:
            if not os.path.exists(file):
                continue
            return os.path.abspath(file)
        return None

    @staticmethod
    def get_platform():
        """Return the platform that is being run on"""
        if os.environ.get("TRAVIS", "false") == "true":
            return CI.TRAVIS_CI
        elif os.environ.get("APPVEYOR", "false") in ("True", "true"):
            # true on Windows, True on Ubuntu
            return CI.APPVEYOR
        else:
            raise RuntimeError("This platform is not currently supported")

    @staticmethod
    def get_os():
        """Return the OS that is being run on"""
        if sys.platform == "win32":
            return CI.WINDOWS
        elif "linux" in sys.platform:  # `linux2` under Python 2
            return CI.LINUX
        elif sys.platform == "darwin":
            return CI.MACOS
        else:
            raise RuntimeError("Unsupported OS: {}".format(sys.platform))

    @staticmethod
    def setup_logger():
        """Return a stdout logger"""
        logger = logging.Logger("CI")
        stdout = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter("%(levelname)s - %(message)s")
        stdout.setFormatter(fmt)
        logger.addHandler(stdout)
        return logger


class Version(object):
    """Parses a semantic version string."""
    def __init__(self, string):
        """
        :param string: semantic version string (major.minor.patch)
        """
        self.major, self.minor, self.patch = map(int, string.split("."))
        self.version = (self.major, self.minor, self.patch)

    def __ge__(self, other):
        return all(elem1 >= elem2 for elem1, elem2 in zip(self.version, other.version))


def ci(python="python", codecov="codecov", coverage_file="coverage.xml"):
    """Run the most common CI tasks"""

    # Build the installation wheel
    dist_type = "bdist_wheel" if not SDIST else "sdist"
    return_code = run_command("{} setup.py {}".format(python, dist_type))
    if return_code != 0:
        print("Building and installing wheel failed.")
        exit(return_code)
    assert os.path.exists(os.path.join("ttkthemes", "tkimg"))

    # Check if an artifact exists
    assert check_wheel_existence()
    print("Wheel file exists.")
    # Install the wheel file
    wheel = [file for file in os.listdir("dist") if file.endswith((".whl", ".tar.gz"))][0]
    wheel = os.path.join("dist", wheel)
    print("Wheel file:", wheel)
    return_code = run_command("{} -m pip install --ignore-installed {}".format(python, wheel))
    if return_code != 0:
        print("Installation of wheel failed.")
        exit(return_code)
    print("Wheel file installed.")

    # Remove all non-essential files
    for to_delete in TO_DELETE:
        rmtree(to_delete)
    # Run the tests on the installed ttkthemes
    return_code = run_command("{} -m nose --with-coverage --cover-xml --cover-package=ttkthemes".format(python))
    if return_code != 0:
        print("Tests failed.")
        exit(return_code)
    print("Tests successful.")
    # Run codecov
    return_code = run_command("{} -f {}".format(codecov, coverage_file))
    if return_code != 0:
        print("Codecov failed.")
        exit(return_code)
    # Successfully finished CI
    exit(0)


def ci_windows():
    """
    Run CI tasks on AppVeyor. CI on AppVeyor is relatively easy, so
    just the general ci() is used.
    """
    ci(
        python="%PYTHON%\\python.exe",
        codecov="%PYTHON%\\Scripts\\codecov.exe",
        coverage_file="C:\\projects\\ttk-themes\\coverage.xml"
    )


def ci_macos():
    """Setup Travis-CI macOS for wheel building"""
    run_command("brew install $PYTHON pipenv || echo \"Installed PipEnv\"")
    command_string = "sudo -H $PIP install "
    for element in DEPENDENCIES + REQUIREMENTS + ["-U"]:
        command_string += element + " "
    run_command(command_string)
    # Build a wheel
    run_command("sudo -H $PYTHON setup.py bdist_wheel")
    assert check_wheel_existence()
    exit(0)


def ci_linux():
    """Setup Travis-CI linux for installation and testing"""
    run_command("sudo apt-get install {}".format(PACKAGES))
    ci()


# Run CI tasks on AppVeyor and Travis-CI (macOS and Linux)
if __name__ == '__main__':
    if sys.platform == "win32":
        ci_windows()
    elif "linux" in sys.platform:   # linux2 on Python 2, linux on Python 3
        ci_linux()
    elif sys.platform == "darwin":
        ci_macos()
    else:
        raise RuntimeError("Invalid platform: ", sys.platform)

