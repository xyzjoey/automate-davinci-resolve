@ECHO OFF
echo Run 'scripts\edit_fusion_text.py' in virtual environment...
echo.
cmd /k python -m tox -e davinci-win -- scripts/edit_fusion_text.py
