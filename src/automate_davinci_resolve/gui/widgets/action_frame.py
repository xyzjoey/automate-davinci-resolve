from customtkinter import CTkButton, CTkFrame, CTkTextbox, ThemeManager

from .named_frame import NamedFrame
from ..definitions import Definitions
from ...app.app import App
from ...app.context import AppContext
from ...app.actions.action_control import ActionControl
from ... import utils


class ActionFrame(CTkFrame):
    def __init__(self, app: App, action: ActionControl, *args, **kw):
        super().__init__(*args, **kw)

        self.app = app
        self.action = action

        self.description_frame = NamedFrame("Description", self)
        self.description_frame.pack(side="top", fill="x")
        self.description_textbox = CTkTextbox(self.description_frame.content_frame, width=500, height=60)
        self.description_textbox.pack(side="top")
        self.description_textbox.insert("0.0", action.description)
        self.description_textbox.configure(state="disabled")

        self.input_form_frame = NamedFrame("Input", self)
        self.input_form_frame.pack(side="top", fill="both", expand=True)

        self.input_widgets = {}

        for field_name, field_info in self.action.input_model.model_fields.items():
            input_definition = Definitions.actions[action.action_type].inputs[field_name]
            widget_type = input_definition.widget_type
            args = input_definition.args

            input_widget = widget_type(
                name=field_info.title,
                **args,
                master=self.input_form_frame.content_frame,
            )
            input_widget.pack(side="left", fill="y", expand=True)

            self.input_widgets[field_name] = input_widget

        self.action_button = CTkButton(self)
        self.action_button.pack(side="bottom", anchor="e")
        self.action_button.configure(command=self.get_action_button_command())
        self.is_start_button = None
        self.set_button(start=True)

    def get_action_button_command(self):
        def command():
            if self.is_start_button:
                input_data = self.get_input_data()
                self.app.start_action(self.action.name, input_data)
            else:
                self.app.stop_action(self.action.name)

        return command

    def get_input_data(self):
        return {field_name: input_widget.get_data() for field_name, input_widget in self.input_widgets.items()}

    def update(self, app_context: AppContext):
        self.set_button(start=(not self.action.is_starting))

        for field_name, input_widget in self.input_widgets.items():
            if hasattr(input_widget, "update"):
                utils.forward_partial_args(input_widget.update)(
                    timeline_context=app_context.resolve_context.timeline_context,
                    timeline_diff=app_context.resolve_context.timeline_diff,
                )

    def set_button(self, start: bool):
        if start == self.is_start_button:
            return

        if start:
            self.action_button.configure(
                text="Start Action",
                fg_color=ThemeManager.theme["CTkButton"]["fg_color"],
                hover_color=ThemeManager.theme["CTkButton"]["hover_color"],
            )
            self.is_start_button = True
        else:
            self.action_button.configure(
                text="Stop Action",
                fg_color="DeepPink3",
                hover_color="DeepPink4",
            )
            self.is_start_button = False
