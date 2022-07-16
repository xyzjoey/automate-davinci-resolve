# automate-davinci-resolve

## Feature
- [x] generate fusion text from .srt subtitle file
- [x] apply fusion text style to tracks

## How to run
Enable external scripting in Davinci Resolve Studio:

Preferences > Generael > External scripting using > Local

```sh
pip install tox # if not yet installed
python -m tox -e davinci-win -- scripts/<script_name>.py
```

```sh
# e.g.
python -m tox -e davinci-win -- scripts/choose_script.py
```

## Reference
- C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\README.txt
- [Davinci_Resolve_18_Reference_Manual.pdf](https://documents.blackmagicdesign.com/UserManuals/DaVinci_Resolve_18_Reference_Manual.pdf)
- [Fusion8_Scripting_Guide.pdf](https://documents.blackmagicdesign.com/UserManuals/Fusion8_Scripting_Guide.pdf)
