import signal
import psutil
import socket
import pycurl
import time
import zipfile
import re
import os
import sys
import json
import subprocess
import select
import shutil
from urllib import urlencode, quote
from StringIO import StringIO    
from time import sleep

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError:
    return False
  return True

def get_formatted_time():
  return time.strftime("%Y-%m-%d %H:%M:%S")

def log(message):
  print("%s: %s" % (get_formatted_time(), message))
  sys.stdout.flush()

def read_file_from_zip(zipfile_path, file_path):
  archive = zipfile.ZipFile(zipfile_path, 'r')
  file_data = archive.read(file_path)
  return file_data

def get_package_name_and_version_from_package_zip(zip_file):
  properties_data = read_file_from_zip(zip_file, 'META-INF/vault/properties.xml')
  package_name = re.findall('<entry key="name">([^<]+)</entry>', properties_data)[0]
  package_version = re.findall('<entry key="version">([^<]+)</entry>', properties_data)
  if(len(package_version) > 0):
    return "%s-%s" % (package_name, package_version[0])
  return package_name

def package_requires_restart(zip_file):
  properties_data = read_file_from_zip(zip_file, 'META-INF/vault/properties.xml')
  requires_restart = re.findall('<entry key="requiresRestart">([^<]+)</entry>', properties_data)
  if(len(requires_restart) > 0 and requires_restart[0].lower() == 'true'):
    return True
  return False

def enable_asset_workflow(base_url, credentials):
  log("Enabling asset workflow")
  set_asset_workflow_status(base_url, credentials, True)
  log("Asset workflow enabled")

def disable_asset_workflow(base_url, credentials):
  log("Disabling asset workflow")
  set_asset_workflow_status(base_url, credentials, False)
  log("Asset workflow disabled")

def set_asset_workflow_status(base_url, credentials, status):
  response = StringIO()
  c = pycurl.Curl()
  c.setopt(c.WRITEFUNCTION, response.write)
  c.setopt(pycurl.USERPWD, credentials)
  c.setopt(c.POSTFIELDS, 'enabled=' + ('true' if status == True else 'false'))
  c.setopt(c.URL, base_url + "/etc/workflow/launcher/config/update_asset_create")
  c.perform()
  c.setopt(c.URL, base_url + "/etc/workflow/launcher/config/update_asset_mod")
  c.perform()
  c.close()

def upload_package(base_url, credentials, file_path, file_name, package_reference):
  install_dir = '/opt/aem/crx-quickstart/install'
  log("Moving package \"%s\" (%s) to %s" % (package_reference, file_name, install_dir))

  if not os.path.exists(install_dir):
    os.makedirs(install_dir)
  
  os.rename(file_path, os.path.join(install_dir, file_name))
  log("Package \"%s\" (%s) moved to %s" % (package_reference, file_name, install_dir))

def wait_until_package_installed(base_url, credentials, package_reference):
  log("Checking package \"%s\" installation..." % (package_reference))

  # Workaround for 6.2 SP1 to check installation status.
  # See https://helpx.adobe.com/experience-manager/6-2/release-notes/sp1.html
  if package_reference.find('aem-service-pkg-6.2.SP1') > -1:
    log("Found 6.2 SP1 package. Monitor error.log to wait for package installation to complete...")
    match = 'from resource TaskResource(url=jcrinstall:/libs/system/aem-service-pkg-6.2.SP1/install/1/updater.aem-service-pkg-1.0.0.jar, entity=bundle:updater.aem-service-pkg, state=UNINSTALL'
    f = subprocess.Popen(['tail', '-F', '/opt/aem/crx-quickstart/logs/error.log'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    while True:
      if p.poll(1):
        if f.stdout.readline().find(match) > -1:
          f.kill()
          log("Package \"%s\" is installed" % (package_reference))
          break
    
  else:
    installed = False
    while not installed:
      package_installation_response = ''
      try:
        package_installation = StringIO()
        c = pycurl.Curl()
        c.setopt(c.WRITEFUNCTION, package_installation.write)
        c.setopt(c.URL, base_url + "/crx/packmgr/list.jsp")
        c.setopt(pycurl.USERPWD, credentials)
        c.perform()
        c.close()
        package_installation_response = package_installation.getvalue()
        package_installation.close()
      except pycurl.error as error:
        log("Package \"%s\" not yet installed. Curl error: %s. Will retry in 10 seconds..." % (package_reference, error))
        sleep(10)
        continue
    
      if not is_json(package_installation_response):
        log("Package \"%s\" not yet installed. Package installation check response: %s. Will retry in 10 seconds..." % (package_reference, package_installation_response))
        sleep(10)
        continue
      
      # Parse packageInstallationResponse as json object and loop through results
      json_response = json.loads(package_installation_response)
      for result in json_response["results"]:
        # break while loop when package is unpacked (i.e. installed)
        package_reference_response = "%s-%s" % (result["name"], result["version"]) if len(result["version"]) > 0 else result["name"]
        if package_reference_response.lower() == package_reference.lower() and 'lastUnpackedBy' in result:
          log("Package \"%s\" is installed" % (package_reference))
          installed = True
          break

      if not installed:
        log("Package \"%s\" not yet installed. Will retry in 10 seconds..." % (package_reference))
        sleep(10)

def import_packages(aem_jar_file_name, port, runmode, username='admin', password='admin', package_dir='packages'):
  log("Start installing packages")

  base_url = "http://localhost:" + port
  credentials = "%s:%s" % (username, password)
  current_dir = os.getcwd()
  author_mode = True if runmode.find('author') > -1 else False

  server_process_id = start_aem_server(aem_jar_file_name, port, runmode)

  if author_mode:
    log("Author mode detected. Setting replication agent...")
    update_author_replication_agent(base_url)
    show_publisher_status(base_url, credentials)

  disable_asset_workflow(base_url, credentials)

  for package_file_name in sorted(os.listdir(os.path.join(current_dir, package_dir))):
    if not package_file_name.endswith(".zip"): 
      log("File \"%s\" is no zip-file" % package_file_name)
      continue

    file_path = os.path.join(current_dir, package_dir, package_file_name)
    log("Starting installation of file \"%s\"" % package_file_name)
    
    package_reference = get_package_name_and_version_from_package_zip(file_path)
    log("Found package name and version in zip file: \"%s\"" % package_reference)
    
    upload_package(base_url, credentials, file_path, package_file_name, package_reference)
    wait_until_package_installed(base_url, credentials, package_reference)

    # Always restart AEM after every package install
    server_process_id = restart_aem_server(server_process_id, aem_jar_file_name, port, runmode)

  log("Finished installing packages.")
  
  log("Start system clean-up...")
  enable_asset_workflow(base_url, credentials)
  stop_aem_server(server_process_id)
  run_compaction('/opt/aem/oak-run.jar', '/opt/aem/crx-quickstart')

def run_compaction(oak_path, aem_quickstart_folder):
  log('Start AEM compaction')

  log('Finding old AEM checkpoints...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'checkpoints', aem_quickstart_folder + '/repository/segmentstore'])
  log('Return code of finding old AEM checkpoints process: %s' % return_code)

  log('Deleting unreferenced AEM checkpoints...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'checkpoints', aem_quickstart_folder + '/repository/segmentstore', 'rm-unreferenced'])
  log('Return code of deleting unreferenced AEM checkpoints process: %s' % return_code)

  log('Running AEM compaction. This may take a while...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'compact', aem_quickstart_folder + '/repository/segmentstore'])
  log('Return code of AEM compaction process: %s' % return_code)

  log('AEM compaction complete')

def start_aem_server(aem_jar_file_name, port, runmode):
  arguments = "file: %s, port: %s, runmode: %s" % (aem_jar_file_name, port, runmode)
  log("Starting AEM with arguments: %s" % arguments)

  # Waits for connection on LISTENER_PORT, and then checks that the returned
  # success message has been received.
  LISTENER_PORT = 50007
  install_process = subprocess.Popen(['java', '-Xms8g', '-Xmx8g', '-Djava.awt.headless=true', 
    '-jar', aem_jar_file_name, '-listener-port', str(LISTENER_PORT), '-r', runmode, '-p', port, '-nofork'])

  # Starting listener
  HOST = ''
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  attempts = 0
  while True:
    attempts = attempts + 1
    log("Trying to start AEM (attempt %s)" % attempts)
    try:
      s.bind((HOST, LISTENER_PORT))
      break
    except Exception as error:
      log("Failed starting server (attempt %s): %s" % (attempts, error))
      if attempts >= 10:
        log("Tried starting server 10 times. Now exiting...")
        sys.exit(1)
      sleep(20)

  s.listen(1)
  conn, addr = s.accept()

  str_result = ""
  while True:
    data = conn.recv(1024)
    if not data:
      log("Failed starting AEM; %s" % arguments)
      install_process.kill()
      sys.exit(1)
    else:
      str_result = str_result + str(data).strip()
      if str_result == 'started':
        log("AEM started; %s" % arguments)
        break

  conn.close()
  return install_process.pid

def stop_aem_server(process_id):
  log("Stopping AEM...")

  parent_aem_process= psutil.Process(process_id)
  for childProcess in parent_aem_process.get_children():
    os.kill(childProcess.pid,signal.SIGINT)

  os.kill(parent_aem_process.pid, signal.SIGINT)
  parent_aem_process.wait()
  log("AEM stopped")
  return True

def restart_aem_server(process_id, aem_jar_file_name, port, runmode):
  log("Restarting AEM...")
  stop_aem_server(process_id)
  new_pid = start_aem_server(aem_jar_file_name, port, runmode)
  log("New AEM process id: %s" % new_pid)
  return new_pid

def update_author_replication_agent(base_url, credentials="admin:admin"):
  # Update Replication Agent
  agent_status = StringIO()
  c = pycurl.Curl()
  c.setopt(c.WRITEFUNCTION, agent_status.write)
  c.setopt(c.URL, base_url + "/etc/replication/agents.author/publish/jcr:content")
  c.setopt(pycurl.USERPWD, credentials)
  post_data = {
    "./sling:resourceType":"cq/replication/components/agent",
    "./jcr:lastModified":"",
    "./jcr:lastModifiedBy":"",
    "_charset_":"utf-8",
    ":status":"browser",
    "./jcr:title":"Default Agent",
    "./jcr:description":"Agent that replicates to the default publish instance.",
    "./enabled":"true",
    "./enabled@Delete":"",
    "./serializationType":"durbo",
    "./retryDelay":"60000",
    "./userId":"",
    "./logLevel":"info",
    "./reverseReplication@Delete":"",
    "./transportUri":"http://publisher:4503/bin/receive?sling:authRequestLogin=1",
    "./transportUser":"admin",
    "./transportPassword":"admin",
    "./transportNTLMDomain":"",
    "./transportNTLMHost":"",
    "./ssl":"",
    "./protocolHTTPExpired@Delete":"",
    "./proxyHost":"",
    "./proxyPort":"",
    "./proxyUser":"",
    "./proxyPassword":"",
    "./proxyNTLMDomain":"",
    "./proxyNTLMHost":"",
    "./protocolInterface":"",
    "./protocolHTTPMethod":"",
    "./protocolHTTPHeaders@Delete":"",
    "./protocolHTTPConnectionClose@Delete":"true",
    "./protocolConnectTimeout":"",
    "./protocolSocketTimeout":"",
    "./protocolVersion":"",
    "./triggerSpecific@Delete":"",
    "./triggerModified@Delete":"",
    "./triggerDistribute@Delete":"",
    "./triggerOnOffTime@Delete":"",
    "./triggerReceive@Delete":"",
    "./noStatusUpdate@Delete":"",
    "./noVersioning@Delete":"",
    "./queueBatchMode@Delete":"",
    "./queueBatchWaitTime":"",
    "./queueBatchMaxSize":""}

  # Form data must be provided already urlencoded.
  postfields = urlencode(post_data)

  # Sets request method to POST,
  # Content-Type header to application/x-www-form-urlencoded
  # and data to send in request body.
  c.setopt(c.POSTFIELDS, postfields)
  c.perform()
  c.close()
  agent_status_response = agent_status.getvalue()
  agent_status.close()

  if agent_status_response.find('<div id="Status">200</div>') == -1:
    log("Updating replication agent failed:")
    log(agent_status_response)
    log("Exiting process...")
    sys.exit(1)
  else:
    log("Updated Author replication agent")

def show_publisher_status(base_url, credentials):
  log("Publisher status:")
  publisher_status = StringIO()
  c = pycurl.Curl()
  c.setopt(c.WRITEFUNCTION, publisher_status.write)
  c.setopt(c.URL, base_url + "/etc/replication/agents.author/publish/jcr:content.json")
  c.setopt(pycurl.USERPWD, credentials)
  c.perform()
  c.close()
  log(publisher_status.getvalue())
