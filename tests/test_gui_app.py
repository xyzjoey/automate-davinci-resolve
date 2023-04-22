from automate_davinci_resolve.gui.app import GuiApp


class TestGuiApp:
    def test_update(self, gui_app):
        gui_app.root.update()
        gui_app.update()
        gui_app.root.quit()
        gui_app.root.withdraw()
