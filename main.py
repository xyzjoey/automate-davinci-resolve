from davinci_resolve_cli.app.app import App
from davinci_resolve_cli.davinci.resolve_app import ResolveApp
from davinci_resolve_cli.gui.app import GuiApp
from davinci_resolve_cli.utils.log import Log


if __name__ == "__main__":
    resolve_app = ResolveApp()
    app = App(resolve_app)
    gui_app = GuiApp(app)

    Log.init()
    Log.add_handler(gui_app.get_log_handler())

    gui_app.mainloop()
