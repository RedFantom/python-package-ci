"""
Author: RedFantom
License: GNU GPLv3
Copyright (c) 2017-2018 RedFantom
"""
from ast import literal_eval
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


def error(message):
    sys.stderr.write(message)


def run_command(command):
    """
    :param command: command to run on os.system
    :return: exit code
    """
    if isinstance(command, list):
        command = " ".join(command)
    print("Running system command: ", command)
    return_info = os.system(command)
    if sys.platform == "win32":
        return return_info
    else:
        return os.WEXITSTATUS(return_info)


class CIError(RuntimeError):
    """Error raised when CI fails"""

    def __init__(self, message):
        RuntimeError.__init__(self, message)


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

    SOURCE = "sdist"
    BINARY = "bdist_wheel"

    PYTHON = {
        APPVEYOR: {
            WINDOWS: "%PYTHON%\\python.exe",
            # TODO: Support AppVeyor Ubuntu images
        },
        TRAVIS_CI: {
            LINUX: "python",
            MACOS: "$PYTHON"
        },
        # TODO: Implement CircleCI support
    }

    TRUE = ("True", "true", True)
    FALSE = ("False", "false", False)

    def __init__(self, platform=None, python=None):
        """
        :param platform: Optional platform override
        :param python: Optional python command override
        """
        self.logger = self.setup_logger()
        self.platform = self.get_platform() if platform is None else platform
        self.os = self.get_os()
        self.python = self.get_python_command() if python is None else python
        if os.environ.get("SDIST", "false") == "true":
            self.type = CI.SOURCE
        else:
            self.type = CI.BINARY
        self.config = ConfigParser()
        self.read_config()
        self.package = self.config["package"]["name"]
        if "working_dir" in self.config["environ"]:
            os.chdir(self.config["environ"]["working_dir"])

    def run_tests(self):
        """Run the tests with nose or as specified in the config file"""
        tests = self.config["package"].get("tests", "nose")

        if tests == "nose":
            command = [self.python, "-m", "nose"]
            if self.config["coverage"].get("enabled", "false") in CI.TRUE:
                command += ["--with-coverage", "--cover-xml"]
                command.append("--cover-package={}".format(self.package))
            return run_command(command)

        if self.config["coverage"].get("enabled", "false") in CI.TRUE:
            raise CIError("Coverage cannot be enabled without nose")

        files = self.parse_config_list(tests)
        for test in files:
            command = [self.python, test]
            result = run_command(command)
            if result != 0:
                error("Test '{}' failed.".format(test))
                return result
        return 0

    def run_coverage(self):
        """Upload the coverage file to the coverage provider"""
        pass

    def build_package(self):
        """Build a wheel or sdist from a package"""
        # Build the installation wheel
        return_code = run_command("{} setup.py {}".format(self.python, self.type))
        if return_code != 0:
            raise CIError("Building package failed")

    def read_config(self):
        """Read the configuration file from disk"""
        path = self.get_config_path()
        if path is None:
            raise CIError("Configuration file could not be found")
        self.config.read_file(path)

    def get_python_command(self):
        """Return the command to run Python in shell"""
        return CI.PYTHON[self.platform][self.os]

    @staticmethod
    def get_built_package_exists():
        """Return whether the wheel or sdist has been built and exists"""
        return len([file for file in os.listdir("dist") if file.endswith((".whl", ".tar.gz"))]) != 0

    @staticmethod
    def get_built_package_file():
        """Return a relative path to the wheel or sdist file"""
        wheel = [file for file in os.listdir("dist") if file.endswith((".whl", ".tar.gz"))][0]
        return os.path.join("dist", wheel)

    def install_package_file(self, file):
        """Install a given package with pip"""
        self.pip_install(["--ignore-installed", "{}".format(self.package)])

    def pip_install(self, pkgs):
        """Install a list of packages with pip"""
        # Install/upgrade the specified packages
        command = [self.python, "-m", "pip", "install", "-U"] + pkgs
        return run_command(command) == 0

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

    @staticmethod
    def parse_config_list(string):
        """
        Return a list of elements found in the config file

        Examples:
            "tests/test1.py" -> ["tests/test1.py"]
            "['test1.py', 'test2.py']" -> ["test1.py", "test2.py"]
        """
        try:
            return literal_eval(string)
        except ValueError:
            return [string]

