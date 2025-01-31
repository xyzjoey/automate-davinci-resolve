from customtkinter import CTk, CTkFont, CTkTextbox

from ..app.app import App
from .log_handler import TextboxLogHandler
from .widgets.action_switcher_frame import ActionSwitcherFrame
from .widgets.named_frame import NamedFrame


class GuiApp:
    def __init__(self, app: App):
        super().__init__()

        self.app = app

        self.root = CTk()
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.title("Davinci Resolve Automation")
        self.root.geometry(f"{1100}x{580}")

        self.action_switcher_frame = ActionSwitcherFrame(app, self.root)
        self.action_switcher_frame.pack(fill="both", expand=True)

        self.log_frame = NamedFrame("Log", self.root)
        self.log_frame.pack(fill="both", expand=True)
        self.log_textbox = CTkTextbox(self.log_frame.content_frame, font=CTkFont(family="Consolas"))
        self.log_textbox.pack(side="top", fill="both", expand=True)
        self.log_textbox.configure(state="disabled")

        self.log_handler = TextboxLogHandler(self.log_textbox)

    def mainloop(self):
        # self.root.update()
        self.periodic_update()
        self.root.mainloop()

    def periodic_update(self):
        self.update()
        self.root.after(500, self.periodic_update)

    def update(self):
        self.app.apply_inputs(self.action_switcher_frame.activated_action, self.action_switcher_frame.activated_action_frame.get_input_data())

        app_context = self.app.update()

        if app_context is not None:
            self.action_switcher_frame.update(app_context)

    def get_log_handler(self):
        return self.log_handler

    def destroy(self):
        self.log_handler.on_destroy()
        self.root.destroy()
