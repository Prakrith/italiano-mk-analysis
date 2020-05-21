import configparser
import os
import sys
from pathlib import Path

# get user home folder
home = str(Path.home())

# init
Config = configparser.ConfigParser()

# find the repository folder
for root, dirs, files in os.walk(home):
    for name in dirs:
        if name == 'Italiano_MK_Analysis':
            # OPEN & write to config.ini
            inifile = open(str(os.getcwd() + os.sep + 'config.ini'), 'w')
            # add platform as section
            Config.add_section(sys.platform)
            # add paths
            Config.set(sys.platform,'ilp', root + os.sep + 'Italiano_MK_Analysis' + os.sep + 'ilps' + os.sep + 'mouse.ilp')
            Config.set(sys.platform, 'mk', root + os.sep + 'Italiano_MK_Analysis' + os.sep + os.sep + 'pipelines' + os.sep + 'mouse.cppipe')
            Config.set(sys.platform, 'rules', root + os.sep + 'Italiano_MK_Analysis' + os.sep + os.sep + 'pipelines' + os.sep + 'cpa_rules' + os.sep + 'mouse_rules.txt')
            Config.set(sys.platform, 'skel', root + os.sep + 'Italiano_MK_Analysis' + os.sep + 'pipelines' + os.sep + 'skel.cppipe')
            Config.set(sys.platform, 'fluo', root + os.sep + 'Italiano_MK_Analysis' + os.sep + 'pipelines' + os.sep + 'fluo.cppipe')
        else:
            sys.exit('Unable to find the Italiano_MK_Analysis repository.')

# get the system applications/programs folder
if sys.platform == 'darwin':
    directory = '/Applications'
elif sys.platform == 'win32':
    directory = 'C:\\Program Files' # (x86)\\

# find ilastik & CellProfiler
for root, dirs, files in os.walk(directory):
    for file in dirs:
        if 'ilastik' in file:
            Config.set(sys.platform, 'ilastik_app', directory + os.sep + file + '/Contents/ilastik-release/run_ilastik.sh')
        else:
            f'Unable to find ilastik in %s.' % {directory}
            
        if 'CellProfiler' in file:
            Config.set(sys.platform, 'cp_app', directory + os.sep + file + '/Contents/MacOS/cp -r -c')
        else:
            f'Unable to find CellProfiler in %s.' % {directory}

# write to config.ini
Config.write(inifile)
inifile.close()
