import sys
from cx_Freeze import setup, Executable

sys.path.insert(0, "src")

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": [
        "os",
        "subprocess",
        "threading",
        "tkinter",
        "typing",
        "wmi",
        "re",
        "dataclasses",
        "serial",
        "winreg",
        "pywintypes",
    ],
    "include_files": [
        "src/",
        "assets/",
    ],
    "includes": ["cnc_ports", "data_classes", "com_wrapper"],
}

setup(
    name="h4cui",
    version="0.1.0",
    description="Wrapper for the hub4com application",
    author="KJ5DTV",
    author_email="wells01440@gmail.com",
    url="https://github.com/kj5dtv/h4cui",
    license="BSD-3-Clause License",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "src/main.py",
            base="Win32GUI",
            icon="assets/kj5dtv.ico",
            target_name="h4cui",
        )
    ],
)
