#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 打包脚本
作者:overflow65537
"""
import PyInstaller.__main__
import os
import site
import shutil
import sys
import subprocess

# 删除dist
if os.path.exists(os.path.join(os.getcwd(), "dist", "MFW")):
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW"))

# 获取参数
# === 构建参数处理 ===
print("[INFO] Received command line arguments:", sys.argv)
if len(sys.argv) != 4:  # 参数校验：平台/架构/版本号
    sys.argv = [sys.argv[0], "win", "x86_64", "v1.0.0"]

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

# 写入版本号
with open(os.path.join(os.getcwd(), "app", "common", "__version__.py"), "w") as f:
    f.write(f'__version__ = "{version}"')


# === 依赖包路径发现 ===
def locate_package(package_name):
    """在 site-packages 中定位指定包的安装路径"""
    for path in site.getsitepackages():
        candidate = os.path.join(path, package_name)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"Can't find {package_name} package")


try:
    # 核心依赖包定位
    maa_path = locate_package("maa")  # MAA 框架核心库
    agent_path = locate_package("MaaAgentBinary")  # 设备连接组件
    darkdetect_path = locate_package("darkdetect")  # 系统主题检测库
    strenum = locate_package("strenum")
except FileNotFoundError as e:
    print(f"[FATAL] Dependency missing: {str(e)}")
    sys.exit(1)

# === PyInstaller 配置生成 ===
base_command = [
    "main.py",
    "--name=MFW",
    "--clean",
    "--noconfirm",  # 禁用确认提示
    # 资源包含规则（格式：源路径{分隔符}目标目录）
    f"--add-data={maa_path}{os.pathsep}maa",
    f"--add-data={agent_path}{os.pathsep}MaaAgentBinary",
    f"--add-data={darkdetect_path}{os.pathsep}darkdetect",
    f"--add-data={os.path.join(os.getcwd(), 'MFW_resource')}{os.pathsep}TEM_files{os.sep}MFW_resource",
    # 自动收集包数据
    "--collect-data=darkdetect",
    "--collect-data=maa",
    "--collect-data=MaaAgentBinary",
    # 隐式依赖声明
    "--hidden-import=darkdetect",
    "--hidden-import=maa",
    "--hidden-import=MaaAgentBinary",
]

# === 平台特定配置 准备阶段 ===
print(f"[DEBUG] Platform: {sys.platform}")

if sys.platform == "darwin":
    if architecture == "x86_64":  # intel CPU
        base_command += [
            "--target-arch=x86_64",
        ]
        print("[DEBUG] Target arch: x86_64")
    elif architecture == "aarch64":  # M1/M2 CPU
        base_command += [
            "--target-arch=arm64",
        ]
        print("[DEBUG] Target arch: aarch64")
    base_command += [
        "--osx-bundle-identifier=com.overflow65537.MFW",
        "--noconsole",  # 禁用控制台窗口
    ]

elif sys.platform == "win32":
    base_command += [
        "--icon=MFW_resource/icon/logo.ico",
        "--distpath",
        os.path.join("dist"),
    ]
    if "ci" not in version:
        base_command += [
            "--noconsole",  # 禁用控制台窗口
        ]

elif sys.platform == "linux":
    base_command += [
        "--noconsole",
    ]  # 禁用控制台窗口
# === 开始构建 ===
print("[INFO] Starting MFW build")
print(f"\n\n[DEBUG] base_command: {base_command}\n\n")
PyInstaller.__main__.run(base_command)

# === 二进制文件处理 ===
# 收集 MAA 的本地库文件
bin_dir = os.path.join(maa_path, "bin")
bin_files = []
for f in os.listdir(bin_dir):
    print(f"[DEBUG] Found binary file: {f}")
    print(f"[DEBUG] Adding binary file: {os.path.join(bin_dir, f)}")
    bin_files.append(f)
    base_command += [f"--add-binary={os.path.join(bin_dir, f)}{os.pathsep}."]


# === 开始构建 ===
print("[INFO] Starting MFW build")
print(f"\n\n[DEBUG] base_command: {base_command}\n\n")
PyInstaller.__main__.run(base_command)

# === 构建后处理 ===
# 复制TEM_files的内容到 dist/MFW 目录
shutil.copytree(
    os.path.join(os.getcwd(), "dist", "MFW", "_internal", "TEM_files"),
    os.path.join(os.getcwd(), "dist", "MFW"),
    dirs_exist_ok=True,
)
# 删除临时目录
shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW", "_internal", "TEM_files"))


for i in bin_files:
    # 复制二进制文件到 dist/MFW 目录
    shutil.copy(
        os.path.join(os.getcwd(), "dist", "MFW", "_internal", i),
        os.path.join(os.getcwd(), "dist", "MFW"),
    )
    # 删除临时文件
    os.remove(os.path.join(os.getcwd(), "dist", "MFW", "_internal", i))

shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW", "_internal", "maa", "bin"))

# 复制README和许可证并在开头加上MFW_前缀
for file in ["README.md", "README-en.md", "LICENSE"]:
    shutil.copy(
        os.path.join(os.getcwd(), file),
        os.path.join(os.getcwd(), "dist", "MFW", f"MFW_{file}"),
    )


# === 构建updater ===
updater_command = [
    "updater.py",
    "--name=MFWUpdater",
    "--onefile",
    "--clean",
    "--noconfirm",  # 禁用确认提示
    "--distpath",
    os.path.join("dist", "MFW"),
]
PyInstaller.__main__.run(updater_command)
