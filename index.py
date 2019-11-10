from http.server import BaseHTTPRequestHandler
#from cowpy import cow
from flask import Flask, Response
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        #message = print('something to say or run here') #import as module?
        #self.wfile.write(message.encode())
        self.wfile.write(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')).encode())
        return
