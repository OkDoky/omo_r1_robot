#! /usr/bin/python

import os, traceback, subprocess
import yaml, shutil

PARAM_PATH = '/root/robot_db/params/'
SAVEMAP_CONF_DIR = PARAM_PATH + 'save_map_config.yaml'
SAVEMAP_CONF_TMP_DIR= SAVEMAP_CONF_DIR + '.tmp'

def check_same_map(map_dir,name):
    return os.path.exists(map_dir+name) 

def change_map_name(map_dir,name):
    tmp = 0
    _find_name = False
    while not _find_name:
        tmp += 1
        _find_name = not check_same_map(map_dir,name+'_%s'%tmp)
    name = name + '_%s'%tmp
    return name

def save_latest_map_config(name):
    map_config = {"SaveMapHandler":{"latest_name":"%s"%name}}
    with open('%s'%SAVEMAP_CONF_TMP_DIR,mode='wb') as f:
        yaml.dump(map_config,f)
        f.close()
        shutil.copy2('%s'%SAVEMAP_CONF_TMP_DIR,'%s'%SAVEMAP_CONF_DIR)

def map_save(name, mode, demension, map_dir):
    def _map_save(map_dir,name):
        try:
            subprocess.Popen('rosrun map_server map_saver --occ 50 --free 40 -f %s%s'%(map_dir,name), shell=True)
            save_latest_map_config(name)
            return True
        except Exception as e:
            return False
    is_exist = True
    text = ''
    success = False
    try:
        if name == '':
            name = 'map'
        is_exist = check_same_map(map_dir,name)
        ## if same map is in map dir
        if is_exist:
            if mode == 0: ## change exist map_name + _1
                name = change_map_name(map_dir,name)
            success = _map_save(map_dir,name)
            if not success: text = 'failed to save map, map_saver failed'
            return success,text
        else:
            success = _map_save(map_dir,name)
            if not success: text = 'failed to save map, map_saver failed'
            return success,text
    except Exception as e:
        text = "failed to save map, %s"%traceback.format_exc()
        return success, text
