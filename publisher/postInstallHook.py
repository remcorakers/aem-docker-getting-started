import pycurl
import os
import sys
import json
from urllib import urlencode, quote
from StringIO import StringIO    
from time import sleep

baseUrl = "http://localhost:4503"
password = "admin:admin"

# Install packages
current_dir = os.getcwd()
print("Current directory " + current_dir)
for file_name in sorted(os.listdir(os.path.join(current_dir, "packages"))):
  if file_name.endswith(".zip"): 
    file_path = os.path.join(current_dir, "packages", file_name)
    print("Starting installation of package \"" + file_name + "\"")
    packageUpload = StringIO()
    c = pycurl.Curl()
    c.setopt(c.WRITEFUNCTION, packageUpload.write)
    c.setopt(c.URL, baseUrl + "/crx/packmgr/service.jsp")
    c.setopt(c.POST, 1)
    c.setopt(pycurl.USERPWD, password)
    c.setopt(c.HTTPPOST, [('file', (c.FORM_FILE, file_path)), ('force', 'true'), ('install', 'true')])
    c.perform()
    c.close()
    packageUploadResponse = packageUpload.getvalue()

    if packageUploadResponse.find('<status code="200">ok</status>') == -1:
      print("Error installing package \"" + file_name + "\".")
      print(packageUploadResponse)
      print("Exiting process...")
      sys.exit(1)
    else:
      print("Package \"" + file_name + "\" uploaded")

      installed = False
      while not installed:
        print("Waiting for package \"" + file_name + "\" installation...")

        packageInstallation = StringIO()
        c = pycurl.Curl()
        c.setopt(c.WRITEFUNCTION, packageInstallation.write)
        c.setopt(c.URL, baseUrl + "/crx/packmgr/list.jsp")
        c.setopt(pycurl.USERPWD, password)
        c.perform()
        c.close()
        packageInstallationResponse = packageInstallation.getvalue()
        
        # Parse packageInstallationResponse as json object and loop through results
        if is_json(packageInstallationResponse):
          jsonResponse = json.loads(packageInstallationResponse)
          for result in jsonResponse["results"]:
            # TODO: build better support to strip package file name order number
            download_name = file_name[2:]
            
            # break while loop when package status is resolved (i.e. installed)
            if result["downloadName"] == download_name and result["resolved"] == True:
              print("Package \"" + file_name + "\" is installed")
              installed = True
              sleep(10)
              break

        sleep(5)
  else:
    print("File \"" + file_name + "\" is no zip-file")
