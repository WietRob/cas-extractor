class Client:
    def send(self):
        pass


def make_client() -> Client:
    return Client()


class Service:
    def init_client(self):
        self.client = make_client()

    def run(self):
        self.init_client()
        self.client.send()
