from easy_di import DI, inject, injected


class Swallow:
    velocity: injected(str)

    def answer(self):
        return f"My airspeed velocity is {self.velocity}"


# this is needed only because the Swallow class is in the __main__ module,
# more realistic scenarios won't need the `inject` function call
inject(__name__)

if __name__ == "__main__":
    DI.register("velocity", "24 miles per hour")
    print(Swallow().answer())
