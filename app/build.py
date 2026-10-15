"""
打包脚本 - 使用PyInstaller将Python程序打包成exe文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / 'app'
IMG_DIR = APP_DIR / 'img'

def clean_build_dirs():
    dirs_to_clean = [ROOT_DIR / 'build', ROOT_DIR / 'dist', ROOT_DIR / '__pycache__']
    for p in dirs_to_clean:
        if p.exists():
            print(f"清理目录: {p}")
            shutil.rmtree(p)
    for spec_file in ROOT_DIR.glob('*.spec'):
        print(f"删除文件: {spec_file}")
        spec_file.unlink()

def install_dependencies():
    print("正在安装依赖包...")
    try:
        req = ROOT_DIR / 'requirements.txt'
        if not req.exists():
            req = APP_DIR / 'requirements.txt'
        if not req.exists():
            print("未找到 requirements.txt，跳过依赖安装（可能已安装）")
            return True
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(req)])
        print("依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        return False

def build_exe():
    print("开始构建exe文件...")
    icon_ico = IMG_DIR / 'favicon.ico'
    icon_png = IMG_DIR / 'logo.png'
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=合同批量生成器',
        f"--icon={str(icon_ico)}",
        f"--add-data={str(IMG_DIR)};img",
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=docx',
        '--hidden-import=jinja2',
        '--hidden-import=numpy',
        '--hidden-import=numpy._distributor_init',
        '--hidden-import=numpy.core._multiarray_umath',
        '--hidden-import=xlrd',
        '--collect-all=pandas',
        '--collect-data=numpy',
        '--collect-submodules=numpy',
        '--collect-all=openpyxl',
        '--collect-all=xlrd',
        '--collect-all=docx',
        str(APP_DIR / 'main.py')
    ]
    if not icon_ico.exists() and not icon_png.exists():
        cmd = [arg for arg in cmd if not str(arg).startswith('--icon')]
    elif not icon_ico.exists() and icon_png.exists():
        cmd = [arg.replace(str(icon_ico), str(icon_png)) if str(arg).startswith('--icon') else arg for arg in cmd]
    try:
        subprocess.check_call(cmd)
        print("exe文件构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

def main():
    print("=" * 50)
    print("合同生成器构建脚本")
    print("=" * 50)
    # 必要文件仅检查入口脚本；依赖文件可选，安装流程中已处理回退
    main_path = APP_DIR / 'main.py'
    if not os.path.exists(main_path):
        print(f"错误: 缺少必要文件 {main_path}")
        return False
    # 依赖文件提示（不阻塞构建）
    root_req = ROOT_DIR / 'requirements.txt'
    app_req = APP_DIR / 'requirements.txt'
    if not root_req.exists() and not app_req.exists():
        print("提示: 未找到 requirements.txt（根或 app 目录），将跳过依赖安装")
    clean_build_dirs()
    if not install_dependencies():
        print("依赖安装失败，构建终止")
        return False
    if not build_exe():
        print("构建失败")
        return False
    print("\n" + "=" * 50)
    print("构建完成！")
    print("=" * 50)
    print(f"exe文件位置: {os.path.abspath(str(ROOT_DIR / 'dist' / '合同批量生成器.exe'))}")
    print("\n使用说明:")
    print("1. 直接双击运行 exe 文件")
    print("2. 将 exe 文件分发给用户即可使用")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n构建过程中发生错误: {e}")
        sys.exit(1)