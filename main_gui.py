from automate_davinci_resolve.app.app import App
from automate_davinci_resolve.davinci.resolve_app import ResolveApp
from automate_davinci_resolve.gui.app import GuiApp
from automate_davinci_resolve.utils.log import Log

if __name__ == "__main__":
    resolve_app = ResolveApp()
    app = App(resolve_app)
    gui_app = GuiApp(app)

    Log.init()
    Log.add_handler(gui_app.get_log_handler())

    gui_app.mainloop()
