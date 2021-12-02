import Ice, sys


def MainApp(Ice.Application):
    def run(self, args):
        broker = self.communicator()
        properties = broker.getProperties("File")
        adapter = broker.createObjectAdapter("MainServiceAdapter")
        main_system = MainServicePrx.checkedCast(adapter)
