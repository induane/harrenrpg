# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\harren\\entry_point.py'],
             pathex=['src\\harren', 'C:\\Users\\User\\Downloads\\harren_rpg-master', 'src\\pytmx', 'src\\pyscroll', ],
             binaries=[],
             datas=[('src\\harren', 'harren')],
             hiddenimports=['pygame', 'log-color', 'six', 'boltons'],
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
          name='harren',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )
