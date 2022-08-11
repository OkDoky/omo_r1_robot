#!/usr/bin/python

from mode_state_context import ModeContext, ConcreteStateNav, ConcreteStateSlam
from bridge_state_context import BridgeAbstractClass
import rospy, roslaunch
import os, traceback, copy
from std_srvs.srv import Empty
from cai_msgs.srv import map_save, str_srv, bridge_control, str_srvResponse, bridge_controlResponse, map_saveResponse
from cai_msgs.msg import robot_state
import yaml, shutil

XML_PATH = '/root/catkin_ws/src/omo_r1_simul/omo_r1_bringup/launch/bridge.launch.xml'
PARAM_PATH = '/root/robot_db/params/'
if not os.path.exists(PARAM_PATH):
    os.mkdir(PARAM_PATH)
BRIDGE_CONF_DIR = PARAM_PATH + 'bridge_config.yaml'
BRIDGE_CONF_TMP_DIR = BRIDGE_CONF_DIR + '.tmp'

def define_bridge_config(mqtt,ros_bridge,multimaster):
    bridge_config = {"BridgeHandler":{"is_mqtt":mqtt,"is_ros_bridge":ros_bridge,"is_multimaster":multimaster}}
    with open('%s'%BRIDGE_CONF_TMP_DIR,mode='wb') as f:
        yaml.dump(bridge_config,f)
        f.close()
        shutil.copy2('%s'%BRIDGE_CONF_TMP_DIR,'%s'%BRIDGE_CONF_DIR)

class CoreNode():
    def __init__(self):
        ## init node
        rospy.init_node("CoreNode")
        self.is_running = True
        self.mode_dir = dict(rospy.get_param("~ModeHandler/mode_dir_dict",{}))
        
        ## [Mode] check keyword in dir keys in param
        for keys in ['nav','slam','device']:
            if not keys in self.mode_dir.keys():
                rospy.logerr('[CoreNode] fail to define %s in params.., shutdown CoreNode'%keys)
                self.is_running = False
                return
        
        ## [Mode] init default concrete state 
        default_mode = rospy.get_param("~ModeHandler/default_mode",'nav')
        default_mode_state = ConcreteStateNav() if default_mode == 'nav' else ConcreteStateSlam()
        
        ## [Mode] init uuid for main launch
        self.launch_uuid = roslaunch.rlutil.get_or_generate_uuid(None, False)
        roslaunch.configure_logging(self.launch_uuid)
        
        ## [Mode] create Mode Context for main mode
        self.mode_context = ModeContext(default_mode_state, self.launch_uuid, self.mode_dir)
        
        ## [Mode] create device launch for essential node for control robot
        self.device_launch = roslaunch.parent.ROSLaunchParent(self.launch_uuid,[self.mode_dir['device']])
        self.device_launch.start()
        
        ## [All] init service server
        self.srvs = []
        # self.srvs.append(rospy.Service("~save_map_as", map_save, self.map_save_cb))
        self.srvs.append(rospy.Service("~brdige_mode_change", bridge_control, self.bridge_mode_change_cb))
        self.srvs.append(rospy.Service("~mode_change", str_srv, self.mode_change_cb))
        
        ## [Mode] init default mode launch
        # self.current_launch = self.init_default_mode_launch(default_mode) ####$$
        
        ## [Bridge] init bridge params
        self.bridge_dir = rospy.get_param("~BridgeHandler/bridge_dir",{})
        
        ## define bridge args, save param in BRIDGE_CONFIG file
        self.bridges = []
        try:
            ## BridgeAbstractClass(uuid,launch dir,name,is_running)
            _mqtt = BridgeAbstractClass(\
                self.launch_uuid,\
                self.bridge_dir['mqtt'],\
                name='mqtt',\
                is_running=rospy.get_param("~BridgeHandler/is_mqtt",False)
                )
            if _mqtt == None: raise Exception
            self.bridges.append(_mqtt)
            _ros_bridge = BridgeAbstractClass(\
                self.launch_uuid,\
                self.bridge_dir['ros_bridge'],\
                name='ros_bridge',\
                is_running=rospy.get_param("~BridgeHandler/is_ros_bridge",False),\
                )
            if _ros_bridge == None: raise Exception
            self.bridges.append(_ros_bridge)
            _multimaster = BridgeAbstractClass(\
                self.launch_uuid,\
                self.bridge_dir['multimaster'],\
                name='multimaster',\
                is_running=rospy.get_param("~BridgeHandler/is_multimaster",False),\
                )
            if _multimaster == None: raise Exception
            self.bridges.append(_multimaster)
            rospy.logwarn("[CoreNode] success to launch bridge files")
            define_bridge_config(_mqtt.is_running, _ros_bridge.is_running, _multimaster.is_running)
        except Exception as e:
            rospy.logwarn("[CoreNode] bridge object is not defined %s"%traceback.format_exc())
        rospy.spin()
        
    # def map_save_cb(self,req):
    #     try:
    #         pass
    #     except Exception as e:
    #         pass
     
    def bridge_mode_change_cb(self,req):
        res = bridge_controlResponse()
        res.success = False; res.code = 0
        try:
            for bridge in self.bridges:
                success, text = False,''
                if bridge.get_name() == 'mqtt':
                    if req.is_mqtt:
                        success, text = bridge.request_turnON()
                    else: 
                        success, text = bridge.request_turnOFF()
                elif bridge.get_name() == 'ros_bridge':
                    if req.is_ros_bridge:
                        success, text = bridge.request_turnON()
                    else: 
                        success, text = bridge.request_turnOFF()
                elif bridge.get_name() == 'multimaster':
                    if req.is_multimaster:
                        success, text = bridge.request_turnON()
                    else: 
                        success, text = bridge.request_turnOFF()
                rospy.logwarn("[CoreNode] %s bridge success %s, text : %s"%(bridge.get_name(),success, text))
            if not success: raise Exception
            rospy.set_param("~BridgeHandler/is_mqtt",req.is_mqtt)
            rospy.set_param("~BridgeHandler/is_ros_bridge",req.is_ros_bridge)
            rospy.set_param("~BridgeHandler/is_multimaster",req.is_multimaster)
            define_bridge_config(req.is_mqtt,req.is_ros_bridge, req.is_multimaster)
                
            res.success = True
            return res
        except Exception as e:
            rospy.logwarn("[CoreNode] bridge callback error %s"%traceback.format_exc())
            res.code = 1
            return res

    def get_state_name(self):
        """
        call mode context func to get current mode name

        Returns:
            string: mode name
        """
        return self.mode_context.request_current_state_name()
    
    def mode_change_cb(self,req):
        """
        change main modecallback

        Args:
            req (string): 'nav','slam','reset'
            change mode requested

        Returns:
            success : True/False
            code : 0 : success
                    1 : communication error while change mode
                    2 : received wrong mode
        """
        res = str_srvResponse()
        res.success = False; res.code = 0
        try:
            if req.req in ['nav','slam']:
                if not req.req == self.get_state_name():
                    rospy.logwarn("[CoreNode] mode change %s -> %s"%(self.get_state_name(), req.req))
                    self.mode_context.request_switch()
                    # self.shutdown_and_launch() ####$$
                else:
                    rospy.logwarn("[CoreNode] maintain current mode %s"%self.get_state_name())
            elif req.req == 'reset':
                rospy.logwarn("[CoreNode] reset mode, current mode is %s"%self.get_state_name())
                self.mode_context.request_reset()
                # self.shutdown_and_launch() ####$$
            else:
                rospy.logwarn("[CoreNode] Wrong mode received")
                res.code = 2
                return res
            res.success = True
            return res
            
        except Exception as e:
            rospy.logwarn("[CoreNode] mode change callback error, %s"%traceback.format_exc())
            res.code = 1
            return res
        
    # def shutdown_and_launch(self):
    #     """
    #     shutdown current launch file and relaunch the commanded mode launch
    #     """
    #     launch = self.current_launch
    #     try:
    #         launch.shutdown()
    #         launch = roslaunch.parent.ROSLaunchParent(self.launch_uuid, [self.mode_dir['%s'%self.get_state_name()]])
    #         launch.start()
    #         self.current_launch = launch
    #         rospy.loginfo('[CoreNode] success to launch %s mode'%self.get_state_name())
    #         return
    #     except Exception as e:
    #         rospy.logerr('[CoreNode] failed to launch %s mode, %s'%(self.get_state_name(),traceback.format_exc()))
            
    # def init_default_mode_launch(self, run_mode):
    #     """
    #     only run at first interface class is initialized
    #     launch default node(when robot boot)

    #     Args:
    #         run_mode (string): default mode for run

    #     Returns:
    #         roslaunch object:  to use when mode change, stop this launch and
    #         relaunch other launch object
    #     """
    #     launch = None
    #     try:
    #         launch = roslaunch.parent.ROSLaunchParent(self.launch_uuid, [self.mode_dir['%s'%run_mode]])
    #         launch.start()
    #         rospy.loginfo("[CoreNode] default mode launched, %s"%run_mode)
    #     except Exception as e:
    #         rospy.logerr("[CoreNode] cannot launch default mode, %s"%traceback.format_exc())
    #     finally:
    #         return launch

if __name__=="__main__":
    ## init class
    cls_ = None
    cls_ = CoreNode()