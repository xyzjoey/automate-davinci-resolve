class UserError(Exception):
    def __init__(self, *args, detailed_error=None, **kw):
        super().__init__(*args, **kw)
        self.detailed_error = detailed_error
