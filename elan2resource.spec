# -*- mode: python -*-

from platform import system


moviepy_path = './venv/lib/python3.6/site-packages/moviepy'

if system() == 'Windows':
    moviepy_path = './venv/Lib/site-packages/moviepy'

block_cipher = None

added_files = [
    ( moviepy_path, 'moviepy' ),
    ( 'src/img/*', 'img' )
]

a = Analysis(['src/elan2resource.py'],
             pathex=['/Users/nickl93/projects/uni/elan2resource'],
             binaries=[],
             datas=added_files,
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
          name='Language Resource Creator',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

app = BUNDLE(exe,
             name='Language Resource Creator.app',
             info_plist={
                'NSHighResolutionCapable': 'True'
             },
             icon='./assets/language.icns')