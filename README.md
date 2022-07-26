# automate-davinci-resolve

## Feature
- [x] generate Text+ from .srt subtitle file
- [x] apply Text+ style to tracks

## How to run
1. Enable external scripting in Davinci Resolve Studio (Preferences > Generael > External scripting using > Local)
2. run `install_requirements.bat`
3. run `start_script_win.bat`

```sh
# what it will show
=============
Start script!
=============
? - print help
a - apply Text+ style from the current timeline clip to track(s)
g - generate Text+ in a new timeline from a .srt subtitle file
q - quit
What do you want to do? [?/a/g/q]:
```

Or run from command:
```sh
python -m tox -e davinci-win -- scripts/<script_name>.py
```

## Reference
- C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt
- [Davinci_Resolve_18_Reference_Manual.pdf](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_18_Reference_Manual.pdf)
- [Fusion8_Scripting_Guide.pdf](https://documents.blackmagicdesign.com/UserManuals/Fusion8_Scripting_Guide.pdf)
