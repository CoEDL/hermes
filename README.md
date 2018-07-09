# Language Resource Creator
Cross-platform utility for turning ELAN (*.eaf) linguistic analysis files and associated media into language resources.

This program can also be used to create language resources from scratch without an ELAN transcription.

The Language Resource Creator was developed by [Nicholas Lambourne](https://ndl.im) using Python3, PyQt5, pydub, and pygame as part of the [UQ Winter Research Scholarship Program](https://employability.uq.edu.au/winter-research). 
It is based on a proof-of-concept built by [Dr Gautier Durantin](http://gdurantin.com/).

Created primarily to produce language resources for the [Social Robot Project](http://www.itee.uq.edu.au/cis/opal/ngukurr) at the [University of Queensland](https://uq.edu.au), developed in collaboration with the [Ngukurr Language Centre](http://www.ngukurrlc.org.au/).

![Process](docs/img/process-flow.png)

![Features](docs/img/features.png)

### Requirements:
- Python 3.6
- Git

### Install/Run Instructions:
#### As a Script
```bash
git clone https://github.com/nicklambourne/elan2resource.git
cd elan2resource
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd src
python3 elan2resource.py
```

#### Build From Source
##### Mac
**N.B: You will have to modify the root dir in the elan2resource.spec file to the absolute path of where you have cloned the repository on your machine.**
```bash
git clone https://github.com/nicklambourne/elan2resource.git
cd elan2resource
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pyinstaller elan2resource.spec --onefile --windowed 
```
The .app executable should appear in elan2resouce/dist.

##### Windows
**N.B: You will have to modify the root dir in the elan2resource.spec file to the absolute path of where you have cloned the repository on your machine.**
```bash
git clone https://github.com/nicklambourne/elan2resource.git
cd elan2resource
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller elan2resource.spec --onefile
```
The .exe file should appear in elan2resource\dist.

### Acknowledgements
Images/Icons courtesy of [Icons8](https://icons8.com/icon/set/play/color).
