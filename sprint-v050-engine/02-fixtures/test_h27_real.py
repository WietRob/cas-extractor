"""Gate A: Real H2.6/2.7 PropagatedSelfAttr test."""


class Client:
    def send(self):
        pass


def make_client() -> Client:
    return Client()


class Service:
    def init_client(self):
        self.client = make_client()

    def run(self):
        self.client.send()
