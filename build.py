from platform import system
import subprocess


command = 'python3 -m venv venv; '

operating_system = system()

if operating_system == 'Darwin':
    command += 'source venv/bin/activate; '
elif operating_system == 'Windows':
    command += 'venv\\Scripts\\activate; '

command += 'pip install -r requirements.txt; '

if operating_system == 'Darwin':
    command += 'pyinstaller elan2resource.spec --onefile --windowed'
elif operating_system == 'Windows':
    command += 'pyinstaller elan2resource.spec --onefile'

subprocess.run(command, shell=True, input=b'y\r\n')