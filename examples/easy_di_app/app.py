from easy_di_app import AbstractMessanger

from easy_di import injected


class MainApplication:
    messanger: injected(AbstractMessanger)

    def do_stuff(self):
        # Any modern IDE will autocomplete the send_message method
        self.messanger.send_message("admin", "Stuff done")

        # A modern IDE will show a warning about 1 not being a `str` - more useful with actual complex data types
        self.messanger.send_message("admin", 1)
