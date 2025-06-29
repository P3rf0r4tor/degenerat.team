from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''
            <form method="post">
                <input type="text" name="test">
                <button type="submit">Send</button>
            </form>
        ''')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print("Полученные данные:", post_data.decode())
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


with open('posts.db.json', 'w') as f:
    f.write('[]')


server = HTTPServer(('localhost', 8000), Handler)
print('Сервер запущен на http://localhost:8000')
server.serve_forever()