import sysconfig
from setuptools import setup, Extension
from setuptools.command.build_py import build_py as _build_py
from Cython.Build import cythonize
import glob
import os

MODULE_NAME = "TAER_Core"
VERSION = "0.0.2"

EXCLUDE_FILES = []
EXCLUDE_DIRS = []

src_dir = "src_pyd"

def get_ext_paths(root_dir, exclude_files, exclude_dirs):
    """get filepaths for compilation"""
    paths = []

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in files:
            if os.path.splitext(filename)[1] != ".py":
                continue
            file_path = os.path.join(root, filename)
            if file_path in exclude_files:
                continue
            paths.append(file_path)
    return paths


# noinspection PyPep8Naming
class build_py(_build_py):
    def find_package_modules(self, package, package_dir):
        ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
        modules = super().find_package_modules(package, package_dir)
        filtered_modules = []
        for pkg, mod, filepath in modules:
            if os.path.exists(filepath.replace(".py", ext_suffix)):
                continue
            filtered_modules.append(
                (
                    pkg,
                    mod,
                    filepath,
                )
            )
        return filtered_modules


setup(
    name=MODULE_NAME,
    version=VERSION,
    # packages=find_packages(),
    ext_modules=cythonize(
        get_ext_paths(src_dir, EXCLUDE_FILES, EXCLUDE_DIRS),
        compiler_directives={"language_level": "3"},
    ),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    cmdclass={"build_py": build_py},
)
