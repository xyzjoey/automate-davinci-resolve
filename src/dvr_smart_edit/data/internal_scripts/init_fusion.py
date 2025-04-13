import asyncio

from dvr_smart_edit.entrypoints import setup_module

setup_module(bmd, resolve, fusion)

from dvr_smart_edit.entrypoints import init_fusion

asyncio.run(init_fusion())
