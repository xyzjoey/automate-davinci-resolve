import os
import platform
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.install import install


class InstallFiles:
    @staticmethod
    def get_data_dir():
        return Path(__file__).parent / "src" / "dvr_smart_edit" / "data"

    @staticmethod
    def get_dvr_program_data_dir():
        current_os = platform.system()

        if current_os == "Windows":
            return Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "Blackmagic Design" / "DaVinci Resolve"
        elif current_os == "Darwin":  # mac
            return Path.home() / "Library" / "Application Support" / "Blackmagic Design" / "DaVinci Resolve"
        else:  # linux
            return Path.home() / ".local" / "share" / "DaVinciResolve"


class PostInstallCommand(install):
    def run(self):
        super().run()
        self.install_files()

    def install_files(self):
        print(f"[dvr_smart_edit] Installing DaVinci Resolve plugin files")

        self.copy_folder(
            InstallFiles.get_data_dir() / "fuses",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Fuses" / "SmartEdit",
        )
        self.copy_folder(
            InstallFiles.get_data_dir() / "scripts" / "Edit",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Scripts" / "Edit" / "SmartEdit",
        )
        self.copy_folder(
            InstallFiles.get_data_dir() / "fusion_configs",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Config" / "SmartEdit",
        )
        self.copy_file(
            InstallFiles.get_data_dir() / "scripts" / "root" / "SmartEdit.scriptlib",
            InstallFiles.get_dvr_program_data_dir() / "Fusion" / "Scripts" / "SmartEdit.scriptlib",
        )

    def copy_folder(self, src_dir, dst_dir):
        if dst_dir.exists() and (dst_dir.is_symlink() or dst_dir.is_file()):
            dst_dir.unlink()

        dst_dir.mkdir(exist_ok=True)

        for path in src_dir.iterdir():
            shutil.copy(path, dst_dir / path.name)

        print(f"[dvr_smart_edit] Copied {src_dir} -> `{dst_dir}`")

    def copy_file(self, src_path, dst_path):
        if dst_path.exists():
            dst_path.unlink()

        shutil.copy(src_path, dst_path)

        print(f"[dvr_smart_edit] Copied {src_path} -> `{dst_path}`")


setup(
    cmdclass={"install": PostInstallCommand},
)
