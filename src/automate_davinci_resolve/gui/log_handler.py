import logging


class TextboxLogHandler(logging.Handler):
    def __init__(self, textbox):
        super().__init__()

        self.textbox = textbox

        self.textbox.tag_config(logging.getLevelName(logging.DEBUG), foreground="gray")
        self.textbox.tag_config(logging.getLevelName(logging.INFO))
        self.textbox.tag_config(logging.getLevelName(logging.WARNING), foreground="yellow")
        self.textbox.tag_config(logging.getLevelName(logging.ERROR), foreground="red")
        self.textbox.tag_config(logging.getLevelName(logging.CRITICAL), foreground="purple")

    def emit(self, record):
        if self.textbox is None:
            return

        msg = self.format(record) + "\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", msg, tags=record.levelname)
        self.textbox.configure(state="disabled")
        self.textbox.see("end")

    def flush(self):
        if self.textbox is None:
            return

        self.textbox.update()

    def on_destroy(self):
        self.textbox = None
