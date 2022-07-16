@ECHO OFF
echo Run 'scripts\choose_script.py' in virtual environment...
echo.
cmd /k python -m tox -e davinci-win -- scripts/choose_script.py
