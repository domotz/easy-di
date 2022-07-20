from easy_di_app import ActualMessanger
from easy_di_app.app import MainApplication

from easy_di import DI


def main():
    DI.register("messanger", ActualMessanger())

    app = MainApplication()
    app.do_stuff()


if __name__ == "__main__":
    main()
