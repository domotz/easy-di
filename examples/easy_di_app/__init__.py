from abc import ABC


class AbstractMessanger(ABC):
    def send_message(self, target: str, message: str):
        raise NotImplementedError()


class ActualMessanger(AbstractMessanger):
    def send_message(self, target: str, message: str):
        print(f"{target}: {message}")
