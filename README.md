# automate-davinci-resolve

## Feature
- [x] import Text+ from .srt subtitle file
- [x] export Text+ to .srt subtitle file
- [x] apply Text+ style to tracks

## How to run
1. Enable external scripting in Davinci Resolve Studio (Preferences > Generael > External scripting using > Local)
2. run `install_requirements.bat`
3. run `start_script_win.bat`

```sh
# what it looks like
=============
Start script!
=============
What do you want to do? [a/c/e/i/m/q/?]: ?
a - apply Text+ style from the current timeline clip to track(s)
c - copy markers from a clip to timeline
e - export all Text+ content in current timeline to a subtitle file
i - import Text+ from a subtitle file in a new timeline
m - monitor and apply Text+ track style continuously
q - quit
? - print help
What do you want to do? [a/c/e/i/m/q/?]:
```

Or run from command:
```sh
python -m tox -e cli-win -- src/davinci_resolve_cli/entry/<script_name>.py
```

## Reference
- Davinci Resolve README.txt (win default path: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt`)
- [Davinci_Resolve_18_Reference_Manual.pdf](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_18_Reference_Manual.pdf)
- [Fusion8_Scripting_Guide.pdf](https://documents.blackmagicdesign.com/UserManuals/Fusion8_Scripting_Guide.pdf)
