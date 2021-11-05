import Ice, sys, IceFlix

def MainApp(Ice.Application):
    def main(self, args):
        properties = broker.getProperties("File")
        adapter = broker.createObjectAdaptaer("MainServiceAdapter")
        adapter = MainServicePkr.checkedCasr(adapter)
