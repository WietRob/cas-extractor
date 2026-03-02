"""
Gate A: H2.6/H2.7 Inter-Method Self-Attr Propagation

Tests that self.attr.method() is resolved when:
- self.attr is assigned in a helper method
- The helper is called before the method call
- The type propagates through the call chain
"""


class Client:
    def send(self):
        pass

    def close(self):
        pass


def make_client() -> Client:
    return Client()


class Service:
    def init_client(self):
        """Helper that assigns self.client"""
        self.client = make_client()

    def prepare(self):
        """Intermediate helper that calls init_client"""
        self.init_client()

    def run(self):
        """Entry point - two-hop chain to assignment"""
        self.prepare()
        # H2.7 should resolve this to Client.send
        self.client.send()
        # H2.7 should resolve this to Client.close
        self.client.close()
