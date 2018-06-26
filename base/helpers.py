import pycurl
import time
import zipfile
import re
import os
import sys
import json
import subprocess
import select
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
  print(get_formatted_time() + ": " + message)

def read_file_from_zip(zipfile_path, file_path):
  archive = zipfile.ZipFile(zipfile_path, 'r')
  file_data = archive.read(file_path)
  return file_data

def get_package_name_from_package_zip(zip_file):
  properties_data = read_file_from_zip(zip_file, 'META-INF/vault/properties.xml')
  package_name = re.findall('<entry key="name">([^<]+)</entry>', properties_data)[0]
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

def upload_package(base_url, credentials, file_path, file_name, package_name):
  log("Uploading package \"" + package_name + "\" (" + file_name + ")...")
  uploaded = False
  while not uploaded:
    try:
      package_upload = StringIO()
      c = pycurl.Curl()
      c.setopt(c.WRITEFUNCTION, package_upload.write)
      c.setopt(c.URL, base_url + "/crx/packmgr/service.jsp")
      c.setopt(c.POST, 1)
      c.setopt(pycurl.USERPWD, credentials)
      c.setopt(c.HTTPPOST, [('file', (c.FORM_FILE, file_path)), ('force', 'true'), ('install', 'true')])
      c.perform()
      c.close()
      package_upload_response = package_upload.getvalue()
      package_upload.close()
    except pycurl.error:
      log("Uploading \"" + package_name + "\" (" + file_name + ") failed. Will retry in 30 seconds...")
      sleep(30)
      continue

    if package_upload_response.find('<status code="200">ok</status>') == -1:
      log("Uploading package \"" + package_name + "\" (" + file_name + ") failed. Will retry in 30 seconds...")
      sleep(30)
    else:
      log("Package \"" + package_name + "\" (" + file_name + ") uploaded")
      uploaded = True

def wait_until_package_installed(base_url, credentials, package_name, file_name):
  log("Checking package \"" + package_name + "\" (" + file_name + ") installation...")

  # Workaround for 6.2 SP1 to check installation status.
  # See https://helpx.adobe.com/experience-manager/6-2/release-notes/sp1.html
  if package_name.find('aem-service-pkg-6.2.SP1') > -1:
    log("Found 6.2 SP1 package. Monitor error.log to wait for package installation to complete...")
    match = 'from resource TaskResource(url=jcrinstall:/libs/system/aem-service-pkg-6.2.SP1/install/1/updater.aem-service-pkg-1.0.0.jar, ' \
            + 'entity=bundle:updater.aem-service-pkg, state=UNINSTALL, attributes=[Bundle-SymbolicName=updater.aem-service-pkg, Bundle-Version=1.0, ' \
            + 'org.apache.sling.installer.api.tasks.ResourceTransformer'
    f = subprocess.Popen(['tail', '-F', '/opt/aem/crx-quickstart/logs/error.log'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = select.poll()
    p.register(f.stdout)

    while True:
      if p.poll(1):
        if f.stdout.readline().find(match) > -1:
          f.kill()
          log("Package \"" + package_name + "\" (" + file_name + ") is installed")
          break
      sleep(1)
    
  else:
    installed = False
    while not installed:
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
      except pycurl.error:
        log("Package \"" + package_name + "\" (" + file_name + ") not yet installed. Will retry in 10 seconds...")
        sleep(10)
        continue
    
      if not is_json(package_installation_response):
        log("Package \"" + package_name + "\" (" + file_name + ") not yet installed. Will retry in 10 seconds...")
        sleep(10)
        continue
      
      # Parse packageInstallationResponse as json object and loop through results
      json_response = json.loads(package_installation_response)
      for result in json_response["results"]:
        # break while loop when package status is resolved (i.e. installed)
        if result["name"] == package_name and result["resolved"] == True:
          log("Package \"" + package_name + "\" (" + file_name + ") is installed")
          installed = True
          break

      if not installed:
        log("Package \"" + package_name + "\" (" + file_name + ") not yet installed. Will retry in 10 seconds...")
        sleep(10)

def import_packages(base_url, username='admin', password='admin', packageDir='packages'):
  log("Start installing packages")

  credentials = username + ":" + password
  current_dir = os.getcwd()

  disable_asset_workflow(base_url, credentials)

  for file_name in sorted(os.listdir(os.path.join(current_dir, packageDir))):
    if not file_name.endswith(".zip"): 
      log("File \"" + file_name + "\" is no zip-file")
      continue

    file_path = os.path.join(current_dir, packageDir, file_name)
    log("Starting installation of file \"" + file_name + "\"")
    
    package_name = get_package_name_from_package_zip(file_path)
    log("Found package name in zip file: " + package_name)
    
    upload_package(base_url, credentials, file_path, file_name, package_name)
    wait_until_package_installed(base_url, credentials, package_name, file_name)

  log("Finished installing packages. Now wait for 5 minutes for all background processes to complete...")
  sleep(300)

  enable_asset_workflow(base_url, credentials)

