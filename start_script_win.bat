@ECHO OFF
echo Run 'scripts\choose_script.py' in virtual environment...
echo.
cmd /k python -m tox -e cli-win -- src/davinci_resolve_cli/entry/choose_script.py
