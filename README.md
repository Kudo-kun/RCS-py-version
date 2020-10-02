# RCS-py-version
A simple python based checker system to run and evaluate C/CPP programs against a set of fixed inputs and outputs. IO files are bundled in the executable using pyinstaller. 
Run `pyinstaller --onefile RCS.spec` in case any modifications are made to the python source code. 
Before running the `.spec` file, make sure the following two statements are present in it: `datas=[("./inputs/*.txt", "./inputs"), ("./outputs/*.txt", "./outputs")]` and `icon='./icon.ico'`. 
Requires Python 3.8+, pyinstaller 4.0+