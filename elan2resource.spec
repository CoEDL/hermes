# -*- mode: python -*-

block_cipher = None

added_files = [
    ( './venv/lib/python3.6/site-packages/moviepy', 'moviepy' ),
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
          name='elan2resource',
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