import pycurl
import os
from urllib import urlencode, quote

baseUrl = "http://localhost:4503"
password = "admin:admin"

# Install packages
current_dir = os.getcwd()
print("Current directory " + current_dir)
for file_name in sorted(os.listdir(os.path.join(current_dir, "packages"))):
  if file_name.endswith(".zip"): 
    file_path = os.path.join(current_dir, "packages", file_name)
    print("Starting installation of package @\"" + file_name + "\"")
    c1 = pycurl.Curl()
    c1.setopt(c1.URL, baseUrl + "/crx/packmgr/service.jsp")
    c1.setopt(c1.POST, 1)
    c1.setopt(pycurl.USERPWD, password)
    c1.setopt(c1.HTTPPOST, [('file', (c1.FORM_FILE, file_path)), ('force', 'true'), ('install', 'true')])
    c1.perform()
    print("Package @\"" + file_name + "\" installed")
    c1.close()
  else:
    print("File @\"" + file_name + "\" is no zip-file")
