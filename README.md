# OMO R1 robot ROS package

Branch : melodic-devel
MainVersionInfo : v0.1.2
DockerVersionInfo : 
  omo/robot/nuc : v0.1.2
  omo/simul/nvidia : v0.1.2

Reference from : https://github.com/omorobot/omoros
Author : OkDoky
Editor : ..

version info
  v0.1.2 : release simul & robot source integration

---
** How to run **
robot : roslaunch omo_r1_bringup core.launch
simul(single_mode) : roslaunch omo_r1_bringup  core.launch is_robot:=false is_single_mode:=true
simul(multi_mode) : roslaunch omo_r1_bringup core.launch is_robot:=false is_single_mode:=false