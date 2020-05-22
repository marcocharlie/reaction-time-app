# Reaction time app
A Python multi-class desktop GUI built with Tkinter to measure the reaction time to auditory stimuli.
## Features
  * insert user data (first name, last name, age)
  * choose how many tests to perform
  * choose experiment version (simple or difficult)
  * press enter to start the experiment
  * press the spacebar as fastest as possible at hearing the beep sound
  * chance to pause and resume the experiment (difficult version only)
  * plot results
  * save results to excel file

## Freezing app to exe file
```
pyinstaller --onefile —windowed --icon=beepbeep.icns —clean BeepBeep.py

python -m auto_py_to_exe
```
