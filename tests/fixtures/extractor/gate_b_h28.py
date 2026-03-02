"""
Gate B: H2.8 Factory Return Inference

Tests that x.method() is resolved when:
- x is assigned from a factory function
- The factory returns ClassName() directly
- No explicit type annotation needed
"""


class Builder:
    def build(self):
        pass

    def reset(self):
        pass


def builder_factory() -> Builder:
    return Builder()


def another_factory():
    """Factory without type annotation but direct return"""
    return Builder()


def main():
    # H2.8 should resolve this to Builder.build
    x = builder_factory()
    x.build()

    # H2.8 should resolve this to Builder.reset
    y = another_factory()
    y.reset()
