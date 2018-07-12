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

def wait_until_package_installed(base_url, credentials, package_reference, file_name):
  log("Checking package \"%s\" (%s) installation..." % (package_reference, file_name))

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
          log("Package \"%s\" (%s) is installed" % (package_reference, file_name))
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
        log("Package \"%s\" (%s) not yet installed. Curl error: %s. Will retry in 10 seconds..." % (package_reference, file_name, error))
        sleep(10)
        continue
    
      if not is_json(package_installation_response):
        log("Package \"%s\" (%s) not yet installed. Package installation check response: %s. Will retry in 10 seconds..." % (package_reference, file_name, package_installation_response))
        sleep(10)
        continue
      
      # Parse packageInstallationResponse as json object and loop through results
      json_response = json.loads(package_installation_response)
      for result in json_response["results"]:
        # break while loop when package status is resolved (i.e. installed)
        package_reference_response = "%s-%s" % (result["name"], result["version"]) if len(result["version"]) > 0 else result["name"]
        if package_reference_response.lower() == package_reference.lower() and result["resolved"] == True:
          log("Package \"%s\" (%s) is installed" % (package_reference, file_name))
          installed = True
          break

      if not installed:
        log("Package \"%s\" (%s) not yet installed. Will retry in 10 seconds..." % (package_reference, file_name))
        sleep(10)

def import_packages(base_url, username='admin', password='admin', package_dir='packages'):
  log("Start installing packages")

  credentials = "%s:%s" % (username, password)
  current_dir = os.getcwd()

  disable_asset_workflow(base_url, credentials)

  for file_name in sorted(os.listdir(os.path.join(current_dir, package_dir))):
    if not file_name.endswith(".zip"): 
      log("File \"%s\" is no zip-file" % file_name)
      continue

    file_path = os.path.join(current_dir, package_dir, file_name)
    log("Starting installation of file \"%s\"" % file_name)
    
    package_reference = get_package_name_and_version_from_package_zip(file_path)
    log("Found package name and version in zip file: \"%s\"" % package_reference)
    
    upload_package(base_url, credentials, file_path, file_name, package_reference)
    wait_until_package_installed(base_url, credentials, package_reference, file_name)

  log("Finished installing packages.")
  enable_asset_workflow(base_url, credentials)

def remove_package_installation_files():
  package_dir = '/opt/aem/crx-quickstart/install'
  log("Removing package files at %s..." % package_dir)
  shutil.rmtree(package_dir)
  log("Package files at %s removed" % package_dir)

def run_compaction(oak_path, aem_quickstart_folder):
  log('Start AEM compaction')

  log('Finding old AEM checkpoints...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'checkpoints', aem_quickstart_folder + '/repository/segmentstore'])
  log('Return code of process: %s' % return_code)

  log('Deleting unreferenced AEM checkpoints...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'checkpoints', aem_quickstart_folder + '/repository/segmentstore', 'rm-unreferenced'])
  log('Return code of process: %s' % return_code)

  log('Running AEM compaction. This may take a while...')
  return_code = subprocess.call(['java', '-Dtar.memoryMapped=true', '-Xms8g', '-Xmx8g', '-jar', oak_path, 'compact', aem_quickstart_folder + '/repository/segmentstore'])
  log('Return code of process: %s' % return_code)

  log('AEM compaction complete')
