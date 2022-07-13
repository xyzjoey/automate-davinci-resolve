from tkinter import Tk, filedialog

class FileIO:
    @staticmethod
    def ask_file(patterns, **kw):
        root = Tk()
        root.withdraw()

        kw["filetypes"] = [(p, p) for p in patterns]

        return filedialog.askopenfilename(**kw)
