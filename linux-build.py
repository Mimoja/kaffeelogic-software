#!/usr/bin/env python2
import os, shutil, tarfile
mypath = os.path.dirname(os.path.abspath(__file__))
mydest = mypath + os.sep + 'dist'
print("Cleaning")
try:
    shutil.rmtree(mydest)
except:
    pass

def tardir(path, archiveName, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for f in os.listdir(path):
            tar_handle.add(os.path.join(path, f), archiveName + os.sep + f, recursive=True)

def ignoreme(a=None,b=None):
    return [f for f in os.listdir(mypath) if not (
            (f.endswith('.py') and f not in ['boot_common.py', 'setup.py', 'WndProcHookMixinCtypes.py', 'linux-install.py'])
            or f in [
                'Release Notes - Kaffelogic Studio.txt',
                'kaffelogic_studio_hints.txt',
                'kaffelogic-artisan-settings.aset',
                'kaffelogic_studio_tips.txt',
                'one-bean.png',
                'media-eject.bmp',
                'lgpl-3.0.txt',
                'toolbar',
                'favicon.ico',
		'ubuntu-readme.txt',
		'ubuntu-dependencies.sh',
		'ubuntu-build.sh',
		'ubuntu-package.sh',
		'linux-build.py',
		'Kaffelogic Studio.spec',
		"kaffelogic-studio.desktop",
		"kaffelogic-studio.xml",
		'linux-desktop-file-install.sh',
		'linux-desktop-file-uninstall.sh'
            ]
        )
    ]
print("Copying")
shutil.copytree(mypath, mydest, ignore=ignoreme)
print("Compressing")
tardir(mydest, 'kaffelogic-studio', mypath + os.sep + 'Output/Kaffelogic Studio 4.4.1.tar.gz')
print("Archive is ready for picking up from Output folder")
