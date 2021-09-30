#!/usr/bin/python3

import logging
import json
from base64 import b64decode
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from args import args
import users
import contest

tokenKey = 'tokenKey123'  # TODO: hide token key

def about():  # Return info about server
    return open('about.json', 'r').read()

class FileUploadRequestHandler(BaseHTTPRequestHandler):
    def send(self, body, code=200):  # Send back a status code with no body
        logging.info(body)
        if type(body) == int:
            self.send_response(body)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:  # Send response body
            body = json.dumps(body).encode('utf-8')
            self.send_response(code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Contest-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body)

    def parse_headers(self):
        try:
            auth, auth_content = self.headers['Authorization'].split(' ', 1)
            if auth == 'Basic':
                username, password = b64decode(
                    auth_content).decode('utf-8').split(':', 1)
                return {'username': username, 'password': password}
            elif auth == 'Bearer':
                return {'token': auth_content}
        except Exception:
            return {}

    def parse_data(self):
        try:
            # Get the size of data
            content_length = int(self.headers['Content-Length'])
            return json.loads(self.rfile.read(content_length).decode(
                'ascii'))  # Get the data itself
        except Exception:
            return {}

    def do_OPTIONS(self):  # Handle POST requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Authorization, Content-Type')
        self.end_headers()

    def do_POST(self):  # Handle POST requests
        path, data, auth = self.path, self.parse_data(), self.parse_headers()
        logging.info(data)
        data.update(auth)
        print(data)

        response = 400
        if path == '/user/register':
            response = users.register(data)
        elif path == '/submit':
            response = contest.submit(data)

        self.send(response)

    def do_GET(self):  # Handle GET requests
        path, data, auth = self.path, self.parse_data(), self.parse_headers()
        logging.info(data)
        data.update(auth)
        print(data)

        response = 400
        if path == '/about':
            response = about()
        elif path == '/user/login':
            response = users.login(data)
        elif path == '/status':
            response = contest.status(data)

        self.send(response)


def run(server_class=ThreadingHTTPServer, handler_class=FileUploadRequestHandler):
    server_address = ('localhost', args.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
 