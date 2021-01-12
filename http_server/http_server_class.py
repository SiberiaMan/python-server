import socket
from email.parser import Parser # Парсер для обработки http - запросов
import json
from http_request_class import Request
from http_response_class import Response

MAX_LINE = 64 * 1024
MAX_HEADERS = 100

class MyHTTPServer:
    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._users = {}

    def serve_forever(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)

        try:
            serv_sock.bind((self._host, self._port))
            serv_sock.listen()

            while True:
                conn, _ = serv_sock.accept()
                print(f'client 1 is connected')
                try:
                    self.serve_client(conn)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()

    def serve_client(self, conn):
        try:
            req = self.parse_request(conn)
            resp = self.handle_request(req)
            self.send_response(conn, resp)
        except ConnectionResetError:
            conn = None
        except Exception as e:
            self.send_error(conn, e)

    def parse_request(self, conn):
        rfile = conn.makefile('rb') # Created socket associated file
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)
        host = headers.get('Host')
        if not host:
            raise Exception('Bad request')
        if host not in (self._server_name, f'{self._server_name}:{self._port}'):
            raise Exception('Not found')
        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise Exception('Request line is too long')
        req_line = str(raw, 'iso-8859-1')
        req_line = req_line.rstrip('\r\n')  # Символы которые требуется устранить
        words = req_line.split()
        if len(words) != 3:  # Ожидаем 3 части
            raise Exception('Malformed request line')
        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise Exception('Unexpected HTTP version')
        return method, target, ver

    def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise Exception('Header line is too long')
            if line in (b'\r\n', b'\n', b''):
                break
            headers.append(line)
            if len(headers) > MAX_HEADERS:
                raise Exception('Too many headers')
        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)

    def handle_request(self, req):
        if req.path == '/users' and req.method == 'POST':
            return self.handle_post_users(req)
        if req.path == '/users' and req.method == 'GET':
            return self.handle_get_users(req)
        if req.path.startswith('/users/'):
            user_id = req.path[len('/users/'):]
            if user_id.isdigit():
                return self.handle_get_users(req, user_id)
        raise Exception('Not found')


    def handle_post_users(self, req):
        user_id = len(self._users) + 1
        self._users[user_id] = {'id': user_id,
                                'name': req.query['name'][0],
                                'age': req.query['age'][0]}
        return Response(204, 'Created')

    def handle_get_users(self, req, user_id=None):
        if not user_id:
            accept = req.headers.get('Accept')
            if 'text/html' in accept:
                contentType = 'text/html; charset=utf-8'
                body = '<html><head></head></body>'
                body += f'<div>Пользователи ({len(self._users)})</div>'
                body += '<ul>'
                for u in self._users.values():
                    body += f'<li>#{u["id"]} {u["name"]}, {u["age"]}</li>'
                body += '</ul>'
                body += '</body></html>'

            elif 'application/json' in accept:
                contentType = 'application/json; charset=utf-8'
                body = json.dumps(self._users)

            else:
                return Response(406, 'Not Acceptable')

        else:
            accept = req.headers.get('Accept')
            if 'text/html' in accept:
                contentType = 'text/html; charset=utf-8'
                body = '<html><head></head></body>'
                body += f'<div>Пользователь {id}</div>'
                body += '<ul>'
                u = self._users[user_id]
                body += f'<li>#{u["id"]} {u["name"]}, {u["age"]}</li>'
                body += '</ul>'
                body += '</body></html>'

            elif 'application/json' in accept:
                contentType = 'application/json; charset=utf-8'
                body = json.dumps(self._users[user_id])

            else:
                return Response(406, 'Not Acceptable')

        body = body.encode('utf-8')
        headers = [('Content-Type', contentType),
                   ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)


    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))

        if resp.headers:
            for (key, value) in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('iso-8859-1'))
        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()

    def send_error(self, conn, err):
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(conn, resp)

