# -*- mode: python -*-

block_cipher = None


a = Analysis(['Kaffelogic Studio.py'],
             pathex=['./'],
             binaries=[],
             datas=[('toolbar', 'toolbar'), ('fonts', 'fonts'), ('favicon.ico', '.'), ('splash.png', '.'), ('logo.png', '.'), ('media-eject.bmp', '.'), ('kaffelogic_studio_hints.txt', '.'), ('kaffelogic_studio_tips.txt', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Kaffelogic Studio',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='favicon.ico' )
