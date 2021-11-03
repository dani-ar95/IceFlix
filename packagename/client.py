import sys, Ice
import IceFlix

with Ice.initialize(sys.argv) as communicator:
    base = communicator.stringToProxy("StreamControllerID:default -p 10000")
    controller = IceFlix.StreamControllerPrx.checkedCast(base)
    if not controller:
        raise RuntimeError("Invalid proxy")

    controller.getSDP("Echate un token bro", 20292)
