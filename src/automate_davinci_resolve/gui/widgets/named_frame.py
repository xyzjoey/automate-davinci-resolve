from customtkinter import CTkFrame, CTkLabel, CTkScrollableFrame


class NamedFrame(CTkFrame):
    def __init__(self, name, *args, **kw):
        super().__init__(*args, **kw)

        self.name_label = CTkLabel(self, text=name)
        self.name_label.pack(side="top", anchor="w")

        self.content_frame = CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True)


class NamedScrollableFrame(CTkFrame):
    def __init__(self, name, *args, **kw):
        super().__init__(*args, **kw)

        self.name_label = CTkLabel(self, text=name)
        self.name_label.pack(side="top", anchor="w")

        self.content_frame = CTkScrollableFrame(self)
        self.content_frame.pack(fill="both", expand=True)
