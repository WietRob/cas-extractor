class Client:
    def send(self):
        pass


def make_client() -> Client:
    return Client()


class Service:
    def init_client(self):
        self.client = make_client()

    def prepare(self):
        self.init_client()

    def run(self):
        self.prepare()
        self.client.send()
