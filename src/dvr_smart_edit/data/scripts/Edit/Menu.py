from dvr_smart_edit.entrypoints import setup_module

setup_module(bmd, resolve, fusion)

from dvr_smart_edit.entrypoints.menus import script_menu

script_menu.smart_edit_menu()
