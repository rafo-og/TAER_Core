import git
import re
import os
import shutil


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
    dist_folder = os.path.join(cwd, "dist")
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    os.system(f"cd {cwd} && python -m build -w")
    for root, folder, files in os.walk(dist_folder):
        for file in files:
            if file.endswith('whl'):
                filepath = os.path.join(root, file)
                os.system(f"python -m pyc_wheel {filepath}")
