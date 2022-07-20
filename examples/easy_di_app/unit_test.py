import unittest
from unittest.mock import call

from easy_di_app.app import MainApplication

from easy_di import DI


class MainApplicationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_messanger = DI.register_mock("messanger")

    def test_do_stuff(self):
        MainApplication().do_stuff()

        self.mock_messanger.send_message.assert_has_calls(
            [
                call("admin", "Stuff done"),
                call("admin", 1),
            ]
        )
