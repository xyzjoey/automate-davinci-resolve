from typing import NamedTuple

from customtkinter import CTkButton, CTkFont, CTkFrame, CTkLabel

from .action_frame import ActionFrame

from ..definitions import Definitions
from ...app.app import App
from ...app.context import AppContext


class ActionUI(NamedTuple):
    tab: CTkButton
    frame: ActionFrame


class ActionSwitcherFrame(CTkFrame):
    def __init__(self, app: App, *args, **kw):
        super().__init__(*args, **kw)

        self.app = app

        self.action_ui: dict[str, ActionUI] = {}
        self.activated_action: str = None
        self.activated_action_frame: ActionFrame = None

        self.sidebar_frame = CTkFrame(self)
        self.sidebar_frame.pack(side="left", fill="y")

        self.main_frame = CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        actions_by_groups = {}

        for action in self.app.actions:
            action_group_name = Definitions.actions[action.action_type].group
            actions_by_groups.setdefault(action_group_name, [])
            actions_by_groups[action_group_name].append(action)

        for action_group_name, actions in actions_by_groups.items():
            tab_group_frame = CTkFrame(self.sidebar_frame)
            tab_group_frame.pack(side="top", padx=20, pady=10)

            action_group_label = CTkLabel(
                tab_group_frame,
                text=action_group_name,
                font=CTkFont(size=16),
            )
            action_group_label.pack()

            for action in actions:
                action_frame = ActionFrame(app, action, self.main_frame)
                action_frame.grid(row=0, column=0, sticky="nswe")

                action_tab = CTkButton(
                    tab_group_frame,
                    text=action.display_name,
                )
                action_tab.pack(side="top")
                action_tab.configure(command=self.get_switch_command(action.name))

                self.action_ui[action.name] = ActionUI(
                    tab=action_tab,
                    frame=action_frame,
                )

        next(iter(self.action_ui.values())).tab.invoke()

    def update(self, app_context: AppContext):
        for action_ui in self.action_ui.values():
            action_ui.frame.update(app_context)

    def get_switch_command(self, action_name):
        def command():
            self.action_ui[action_name].frame.tkraise()
            self.activated_action = action_name
            self.activated_action_frame = self.action_ui[action_name].frame

        return command
