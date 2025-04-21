import os
import platform
import shutil
from argparse import ArgumentParser
from pathlib import Path


class InstallFiles:
    @staticmethod
    def get_data_dir():
        return Path(__file__).parent.parent / "src" / "dvr_smart_edit" / "data"

    @staticmethod
    def get_dvr_program_data_dir():
        current_os = platform.system()

        if current_os == "Windows":
            return Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Blackmagic Design" / "DaVinci Resolve"
        elif current_os == "Darwin":  # mac
            return Path.home() / "Library" / "Application Support" / "Blackmagic Design" / "DaVinci Resolve"
        else:  # linux
            return Path.home() / ".local" / "share" / "DaVinciResolve"


class Main:
    def __init__(self):
        argparser = ArgumentParser()
        argparser.add_argument("--force", "-f", action="store_true")
        args = argparser.parse_args()

        self.force = args.force
        self.install_files()

    def install_files(self):
        print(f"[dvr_smart_edit] Installing DaVinci Resolve plugin files")

        self.create_dir_symlink(
            InstallFiles.get_data_dir() / "fuses",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Fuses" / "SmartEdit",
        )
        self.create_dir_symlink(
            InstallFiles.get_data_dir() / "scripts" / "Edit",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Scripts" / "Edit" / "SmartEdit",
        )
        self.create_dir_symlink(
            InstallFiles.get_data_dir() / "fusion_configs",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Config" / "SmartEdit",
        )
        self.create_file_symlink(
            InstallFiles.get_data_dir() / "scripts" / "root" / "SmartEdit.scriptlib",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Scripts" / "SmartEdit.scriptlib",
        )
        # dev only
        self.create_dir_symlink(
            InstallFiles.get_data_dir() / "macros" / "Generators",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Templates" / "Edit" / "Generators" / "SmartEdit",
        )

    def create_dir_symlink(self, src_path, dst_path):
        self.create_symlink(src_path, dst_path, target_is_directory=True)

    def create_file_symlink(self, src_path, dst_path):
        self.create_symlink(src_path, dst_path, target_is_directory=False)

    def create_symlink(self, src_path, dst_path, **kw):
        if not dst_path.exists() and not dst_path.is_symlink():
            dst_path.symlink_to(src_path, **kw)
            print(f"[dvr_smart_edit] Created link `{dst_path}`")
        elif self.force:
            if dst_path.is_file() or dst_path.is_symlink():
                dst_path.unlink()
            else:
                shutil.rmtree(dst_path)
            dst_path.symlink_to(src_path, **kw)
            print(f"[dvr_smart_edit] Created link `{dst_path}`")
        else:
            print(f"[dvr_smart_edit] Cannot create link `{dst_path}` (already exists)")


if __name__ == "__main__":
    Main()
