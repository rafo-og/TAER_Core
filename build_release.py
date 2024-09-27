import git
import re
import os
import shutil


def obfuscate(src_dir, dst_dir):
    """
    Copies all .pyc files from src_dir to dst_dir, maintaining the directory structure.

    :param src_dir: The source directory to search for .pyc files.
    :param dst_dir: The destination directory where .pyc files should be copied.
    """
    # Walk through the source directory
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            # Get the full path of the source .pyc file
            src_file_path = os.path.join(root, file)

            # Calculate the relative path to preserve the folder structure
            relative_path = os.path.relpath(root, src_dir)

            # Destination folder
            dst_folder = os.path.join(dst_dir, relative_path)

            # Ensure the destination folder exists
            os.makedirs(dst_folder, exist_ok=True)

            # Destination path for the obfuscated file
            dst_file_path = os.path.join(dst_folder, file)

            # Obfuscate the file
            os.system(
                f"pyminifier -o {dst_file_path} --obfuscate --obfuscate-import-methods --obfuscate-builtins --nonlatin {src_file_path}"
            )


def update_version(file_path, new_version):
    # Open the file for reading and writing
    with open(file_path, "r") as file:
        content = file.read()

    # Use regex to find and replace the version string
    new_content = re.sub(
        r'__version__\s*=\s*["\'].*?["\']', f'__version__="{new_version}"', content
    )

    # Write the updated content back to the file
    with open(file_path, "w") as file:
        file.write(new_content)


def get_git_version(repopath):
    # Writes latest git version info to 'version.txt'
    r = git.repo.Repo(cwd, search_parent_directories=True)
    version_info = r.git.describe("--tags", "--abbrev=0")
    version_info = version_info.removeprefix("v")
    return version_info


if __name__ == "__main__":
    cwd = os.path.dirname(os.path.abspath(__file__))
    version = get_git_version(cwd)
    print(f"Compiling version v{version}...")
    filepath = os.path.join(cwd, "src/TAER_Core/__init__.py")
    update_version(filepath, version)
    src_folder = os.path.join(cwd, "src")
    dst_folder = os.path.join(cwd, "tmp/src_obf")
    obfuscate(src_folder, dst_folder)
    os.system(f"cd {cwd} && python -m build -w")
    shutil.rmtree(dst_folder)
