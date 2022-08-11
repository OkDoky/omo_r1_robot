#! /usr/bin/python
import traceback
import roslaunch

class BridgeAbstractClass():

    def __init__(self,uuid,dir,name='default',is_running=False):
        try:
            self._name = name
            self.is_running = is_running
            self.is_used = False
            self._uuid = uuid
            self._dir = dir
            self.launch = None
            
            if self.is_running:
                success,error_txt = self.request_turnON()
                if not success: return None
        except Exception as e:
            return None

    def get_name(self):
        return self._name

    def request_turnON(self):
        success = False
        try:
            if self.is_running and self.is_used:
                text = 'already running'
                success = True
                return success, text
            self.is_running = True
            self.is_used = True
            self.launch = roslaunch.parent.ROSLaunchParent(self._uuid,[self._dir])
            print("%s says: turn on"%self.get_name())
            self.launch.start()
            success = True
            return success,''
        except Exception as e:
            text = traceback.format_exc()
            return success,text

    def request_turnOFF(self):
        success = False
        try:
            if not self.is_used or self.launch == None:
                print("%s says: cannot shutdown"%self.get_name())
                success = True
                return success, 'already shutdown'
            self.is_running = False
            print("%s says: turn off"%self.get_name())
            self.launch.shutdown()
            success = True
            return success,''
        except Exception as e:
            text = traceback.format_exc()
            return success, text
