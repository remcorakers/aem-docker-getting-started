import subprocess
import signal
import os
import sys
import psutil
from optparse import OptionParser
from time import sleep

# Argument definition
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-i", "--install_file", dest="filename", help="AEM install file")
parser.add_option("-r", "--runmode", dest="runmode", help="Run mode for the installation")
parser.add_option("-p", "--port", dest="port", help="Port for instance")

options, args = parser.parse_args()
option_dic = vars(options)

# Copy out parameters
print(option_dic)
print(option_dic['filename'])
file_name = option_dic.setdefault('filename', 'cq-publish-4503.jar')
runmode = option_dic.setdefault('runmode', 'publish')
port = option_dic.setdefault('port', '4503')

# Waits for connection on LISTENER_PORT, and then checks that the returned
# success message has been recieved.
LISTENER_PORT = 50007
install_process = subprocess.Popen(['java', '-Xms4096m', '-Xmx4096m', '-Djava.awt.headless=true', 
  '-jar', file_name, '-listener-port', str(LISTENER_PORT), '-r', runmode, '-p', port])

# Starting listener
import socket
HOST = ''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, LISTENER_PORT))
s.listen(1)
conn, addr = s.accept()

successful_start = False
str_result = ""
while 1:
  data = conn.recv(1024)
  if not data:
    break
  else:
    str_result = str_result + str(data).strip()
    if str_result == 'started':
      successful_start = True
      break
conn.close()

# Post install hook
post_install_hook = "postInstallHook.py"
if os.path.isfile(post_install_hook):
  print("Executing post install hook")
  return_code = subprocess.call(["python", post_install_hook])
  print(return_code)
  print("Sleeping for 3 seconds...")
  sleep(3)
else:
  print("No install hook found")

print("Stopping instance")

# If the success message was received, attempt to close all associated processes.
if successful_start == True:
  parent_aem_process= psutil.Process(install_process.pid)
  for childProcess in parent_aem_process.get_children():
    os.kill(childProcess.pid,signal.SIGINT)

  os.kill(parent_aem_process.pid, signal.SIGINT)
  install_process.wait()
  sys.exit(0)
else:
  install_process.kill()
  sys.exit(1)