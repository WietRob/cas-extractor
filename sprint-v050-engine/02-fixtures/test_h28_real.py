"""Gate B: Real H2.8 FactoryReturn test."""


class Builder:
    def build(self):
        pass


def builder_factory():
    return Builder()


def main():
    x = builder_factory()
    x.build()
