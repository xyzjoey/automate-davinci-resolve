@ECHO OFF
echo Setup virtual environment...
echo.
cmd /k python -m tox run -e gui-win
