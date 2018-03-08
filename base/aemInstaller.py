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
optDic = vars(options)

# Copy out parameters
print(optDic)
print(optDic['filename'])
fileName = optDic.setdefault('filename', 'cq-publish-4503.jar')
runmode = optDic.setdefault('runmode', 'publish')
port = optDic.setdefault('port', '4503')

# Waits for connection on LISTENER_PORT, and then checks that the returned
# success message has been recieved.
LISTENER_PORT = 50007
installProcess = subprocess.Popen(['java', '-Xms4096m', '-Xmx4096m', '-Djava.awt.headless=true', 
  '-jar', fileName, '-listener-port', str(LISTENER_PORT), '-r', runmode, '-p', port])

# Starting listener
import socket
HOST = ''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, LISTENER_PORT))
s.listen(1)
conn, addr = s.accept()

successfulStart = False
strResult = ""
while 1:
  data = conn.recv(1024)
  if not data:
    break
  else:
    strResult = strResult + str(data).strip()
    if strResult == 'started':
      successfulStart = True
      break
conn.close()

# Post install hook
postInstallHook = "postInstallHook.py"
if os.path.isfile(postInstallHook):
  print("Executing post install hook")
  returncode = subprocess.call(["python", postInstallHook])
  print(returncode)
  print("Sleeping for 3 seconds...")
  sleep(3)
else:
  print("No install hook found")

print("Stopping instance")

# If the success message was received, attempt to close all associated processes.
if successfulStart == True:
  parentAEMprocess= psutil.Process(installProcess.pid)
  for childProcess in parentAEMprocess.get_children():
    os.kill(childProcess.pid,signal.SIGINT)

  os.kill(parentAEMprocess.pid, signal.SIGINT)
  installProcess.wait()
  sys.exit(0)
else:
  installProcess.kill()
  sys.exit(1)