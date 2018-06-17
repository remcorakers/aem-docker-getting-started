import pycurl
import os
from urllib import urlencode, quote

baseUrl = "http://localhost:4502"
password = "admin:admin"

# Update Replication Agent
c = pycurl.Curl()
c.setopt(c.URL, baseUrl + "/etc/replication/agents.author/publish/jcr:content")
c.setopt(pycurl.USERPWD, password)
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

# Print Publisher status
print("Checking Agent")
c = pycurl.Curl()
c.setopt(c.URL, baseUrl + "/etc/replication/agents.author/publish/jcr:content.json")
c.setopt(pycurl.USERPWD, password)
c.perform()

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
