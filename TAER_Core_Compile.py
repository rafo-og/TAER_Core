import os
import shutil
import subprocess
from setuptools import setup, Extension
from Cython.Build import cythonize
import flit

PROJECT_NAME = "TAER_Core"

def ensure_dependencies():
    try:
        import Cython
        import setuptools
        import build
    except ImportError:
        os.system("pip install --upgrade cython setuptools build")


def convert_to_pyd(src_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for root, dirs, files in os.walk(src_dir):
        for dir in dirs:
            dest_dir_path = os.path.join("TAER_Core", dir)
            if (
                not os.path.exists(dest_dir_path)
                and dir != "__pycache__"
                and dir != "logs"
            ):
                os.makedirs(dest_dir_path)
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                dest_path = os.path.join(dest_dir, os.path.relpath(file_path, src_dir))
                dest_dir_path = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir_path):
                    os.makedirs(dest_dir_path)
                shutil.copy(file_path, dest_path)

    # Build .pyd files using setup.py
    os.system("python setup.py build_ext --inplace bdist_wheel")

    # Cleanup
    clean_after()

def clean_before():
    clean_after()
    shutil.rmtree("dist", ignore_errors=True)

def clean_after():
    shutil.rmtree("build", ignore_errors=True)
    shutil.rmtree("src_pyd", ignore_errors=True)
    shutil.rmtree(f"{PROJECT_NAME}", ignore_errors=True)
    shutil.rmtree(f"{PROJECT_NAME}.egg-info", ignore_errors=True)

def main():
    # Ensure necessary tools are installed within the virtual environment
    ensure_dependencies()

    # Clean previous folders if exists
    clean_before()
    shutil.rmtree("dist", ignore_errors=True)

    # Convert .py files to .pyd files
    src_dir = "./src/TAER_Core"
    dest_dir = "./src_pyd/TAER_Core"
    convert_to_pyd(src_dir, dest_dir)


if __name__ == "__main__":
    main()
