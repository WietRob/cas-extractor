class Builder:
    def build(self):
        pass


def builder_factory() -> Builder:
    return Builder()


def main():
    x = builder_factory()
    x.build()
