import os
import sys
import logging

sys.path.append(os.path.split(os.getcwd())[0])
sys.path.append(os.getcwd())

import command
from AVMaster.vm_manager import VMManager

class Command_START_VM(command.ServerCommand):
    """ starts a vm """

    def execute(self, args):
        """ server side """
        logging.debug("    CS Execute")
        assert self.vm, "null self.vm"

        #TODO: start a VM: self.vm
        VMManager.execute(self.vm, "startup")

        return True, "I'm doing Science and I'm alive"
