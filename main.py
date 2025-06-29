from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time
import json
from urllib.parse import parse_qs

HOST = 'localhost'
PORT = 8000

# Загружаем треды
try:
    with open('posts.db.json', 'r') as f:
        THREADS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    THREADS = []  # Инициализируем пустой список


def save_threads():
    with open('posts.db.json', 'w') as f:
        json.dump(THREADS, f)


def generate_new_thread_form():
    return '''
    <h3>Создать новый тред</h3>
    <form method="POST" action="/new_thread" class="post-form">
        <label>Заголовок:<br><input type="text" name="title" required></label><br>
        <label>Автор (по умолчанию Аноним):<br><input type="text" name="author"></label><br>
        <label>Сообщение:<br><textarea name="text" required></textarea></label><br>
        <button type="submit">Создать тред</button>
    </form>
    '''


def generate_threads_list():
    sorted_threads = sorted(
        THREADS,
        key=lambda t: t['posts'][-1]['timestamp'],
        reverse=True
    )
    html = '<h2>Треды</h2><div style="display: flex; flex-direction: column; gap: 1rem;">'
    for thread in sorted_threads:
        first_post = thread['posts'][0]
        text_preview = first_post['text'][:100] + ('...' if len(first_post['text']) > 100 else '')
        last_post_time = thread['posts'][-1]['timestamp']
        html += f'''
        <div style="background-color: #eceabe; padding: 1rem; border-radius: 8px;">
            <a href="/thread/{thread["id"]}" style="color: black; text-decoration: none;">
                <strong>{thread["title"]}</strong><br>
                <small>{text_preview} (посл. {last_post_time})</small>
            </a>
        </div>
        '''
    html += '</div>'
    return html


def generate_thread_page(thread_id):
    thread = next((t for t in THREADS if t['id'] == thread_id), None)
    if not thread:
        return None

    html = f'<h2>{thread["title"]}</h2>'
    for post in thread['posts']:
        html += f'''
        <div class="post-block">
            <strong>{post["author"]}</strong> ({post["timestamp"]})<br>
            <p>{post["text"]}</p>
        </div>
        '''

    html += f'''
    <form method="POST" action="/reply" class="post-form">
        <input type="hidden" name="thread_id" value="{thread_id}">
        <label>Автор (по умолчанию Аноним):<br><input type="text" name="author"></label><br>
        <label>Сообщение:<br><textarea name="text" required></textarea></label><br>
        <button type="submit">Отправить</button>
    </form>
    '''

    return html

class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Отключаем стандартные логи сервера
        return

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            with open('index.html', 'rb') as f:
                content = f.read()
            index_html = content.decode('utf-8')

            new_thread_form = generate_new_thread_form()
            threads_list = generate_threads_list()

            full_page = index_html.replace('</main>', f'{new_thread_form}{threads_list}</main>')
            self.wfile.write(full_page.encode('utf-8'))

        elif self.path.startswith('/thread/'):
            try:
                thread_id = int(self.path.split('/')[-1])
                thread_html = generate_thread_page(thread_id)
                if thread_html:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    with open('index.html', 'rb') as f:
                        content = f.read()
                    index_html = content.decode('utf-8')

                    full_page = index_html.replace('</main>', f'{thread_html}</main>')
                    self.wfile.write(full_page.encode('utf-8'))
                else:
                    self.send_error(404, 'Thread not found')
            except ValueError:
                self.send_error(400, 'Invalid thread ID')

        else:
            self.send_error(404, 'Not Found')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        data = parse_qs(body)

        now = time.strftime('%Y-%m-%d %H:%M')

        if self.path == '/new_thread':
            title = data.get('title', [''])[0].strip()
            author = data.get('author', [''])[0] or 'Аноним'
            text = data.get('text', [''])[0].strip()

            if not title or not text:
                print("Ошибка: отсутствуют обязательные поля")
                self.send_error(400, 'Missing fields')
                return

            thread_id = len(THREADS) + 1
            THREADS.append({
                'id': thread_id,
                'title': title,
                'posts': [{
                    'author': author,
                    'text': text,
                    'timestamp': now
                }]
            })
            save_threads()
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()

        elif self.path == '/reply':
            thread_id = int(data.get('thread_id', [0])[0])
            author = data.get('author', [''])[0] or 'Аноним'
            text = data.get('text', [''])[0].strip()

            if not text or not thread_id:
                print("Ошибка: отсутствуют обязательные поля в reply")
                self.send_error(400, 'Missing fields')
                return

            thread = next((t for t in THREADS if t['id'] == thread_id), None)
            if thread:
                thread['posts'].append({
                    'author': author,
                    'text': text,
                    'timestamp': now
                })
                save_threads()
                self.send_response(302)
                self.send_header('Location', f'/thread/{thread_id}')
                self.end_headers()
            else:
                self.send_error(404, 'Thread not found')


if __name__ == '__main__':
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Server started on http://localhost:8000')
    httpd.serve_forever()