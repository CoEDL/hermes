# -*- mode: python -*-

from platform import system


block_cipher = None

added_files = [
    ( 'src/img/*', 'img' )
]

root_dir = '/Users/nickl93/projects/uni/elan2resource'
entry_point = 'src/elan2resource.py'

if system() == 'Windows':
    root_dir = 'C:\\Users\\s4261833\\PycharmProjects\\elan2resource'
    entry_point = 'src\\elan2resource.py'
    added_files.append(( 'venv/Lib/site-packages/PyQt5/sip.pyd', 'PyQt5'))

a = Analysis([entry_point],
             pathex=[root_dir],
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
          console=False )

app = BUNDLE(exe,
             name='Language Resource Creator.app',
             info_plist={
                'NSHighResolutionCapable': 'True'
             },
             icon='./assets/language.icns')