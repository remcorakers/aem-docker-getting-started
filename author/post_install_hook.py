import pycurl
import os
import sys
import subprocess
from helpers import log, import_packages, remove_package_installation_files
from urllib import urlencode, quote
from StringIO import StringIO    

base_url = "http://localhost:4502"
password = "admin:admin"

# Update Replication Agent
agent_status = StringIO()
c = pycurl.Curl()
c.setopt(c.WRITEFUNCTION, agent_status.write)
c.setopt(c.URL, base_url + "/etc/replication/agents.author/publish/jcr:content")
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

# Showing Publisher status
log("Publisher status:")
publisher_status = StringIO()
c = pycurl.Curl()
c.setopt(c.WRITEFUNCTION, publisher_status.write)
c.setopt(c.URL, base_url + "/etc/replication/agents.author/publish/jcr:content.json")
c.setopt(pycurl.USERPWD, password)
c.perform()
c.close()
log(publisher_status.getvalue())

# Install packages
import_packages(base_url)
remove_package_installation_files()
