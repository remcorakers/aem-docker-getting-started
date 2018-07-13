import sys
import helpers
from optparse import OptionParser

# Argument definition
usage = "usage: %prog [options] arg"
parser = OptionParser(usage)
parser.add_option("-i", "--install_file", dest="filename", help="AEM install file")
parser.add_option("-r", "--runmode", dest="runmode", help="Run mode for the installation")
parser.add_option("-p", "--port", dest="port", help="Port for instance")

options, args = parser.parse_args()
option_dic = vars(options)
file_name = option_dic.setdefault('filename', 'cq-publish-4503.jar')
runmode = option_dic.setdefault('runmode', 'publish')
port = option_dic.setdefault('port', '4503')

# Copy out parameters
helpers.log("aem_installer.py called with params: %s" % option_dic)

helpers.import_packages(file_name, port, runmode)

sys.exit(0)
