# RCS-py-version
A simple python based checker system to run and evaluate C/C++ programs against a set of fixed inputs and outputs. IO files are bundled in the executable using pyinstaller.
Run `pyinstaller --onefile RCS.spec` in case any modifications are made to the python source code. (Requires Python 3.8, pyinstaller 4.0 or higher)
To run the judge in a linux environment, recompile the whole source code using pyinstaller and make the following change `datas=[("./inputs/*.txt", "./inputs"), ("./outputs/*.txt", "./outputs")]`. Finally, run `pyinstaller --onefile RCS.spec` to create the executable.
