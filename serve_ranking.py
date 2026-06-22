import os, json, re, sys, threading, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKED_FILE = os.path.join(BASE_DIR, "tracked_companies.json")
REPORTS_DIR = os.path.join(BASE_DIR, "relatorios")
REPORTS_LOG = os.path.join(BASE_DIR, "reports_generated.json")

# Importa funcoes de geracao de relatorio
sys.path.insert(0, BASE_DIR)
from generate_report import generate_report, save_report_as_pdf

def load_tracked():
    with open(TRACKED_FILE, encoding='utf-8') as f:
        return json.load(f)

def load_reports_log():
    if os.path.exists(REPORTS_LOG):
        with open(REPORTS_LOG, encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_reports_log(reports_set):
    with open(REPORTS_LOG, 'w', encoding='utf-8') as f:
        json.dump(sorted(reports_set), f, indent=2, ensure_ascii=False)

def find_company(nome):
    companies = load_tracked()
    for c in companies:
        if c.get('name', '') == nome:
            return c
    return None

def company_has_report(nome):
    safe = re.sub(r'[\\/*?:"<>|]', '', nome[:50]).strip().replace(' ', '_')
    pdf_path = os.path.join(REPORTS_DIR, f"{safe}_relatorio.pdf")
    return os.path.exists(pdf_path)

class RankingHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == '/gerar_relatorio':
            nome = params.get('nome', [None])[0]
            if not nome:
                self.send_json({'status': 'erro', 'msg': 'Parametro nome obrigatorio'})
                return
            self.send_json(self.gerar_relatorio(nome))
            return

        if path == '/status_relatorio':
            nome = params.get('nome', [None])[0]
            if not nome:
                self.send_json({'status': 'erro', 'msg': 'Parametro nome obrigatorio'})
                return
            has = company_has_report(nome)
            self.send_json({'status': 'ok', 'existe': has, 'nome': nome})
            return

        if path == '/lista_sem_relatorio':
            reports_set = load_reports_log()
            companies = load_tracked()
            sem = [c['name'] for c in companies if c['name'] not in reports_set]
            self.send_json({'status': 'ok', 'total': len(sem), 'empresas': sem})
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/gerar_relatorio':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = parse_qs(body)
            nome = params.get('nome', [None])[0]
            if not nome:
                self.send_json({'status': 'erro', 'msg': 'Parametro nome obrigatorio'})
                return
            self.send_json(self.gerar_relatorio(nome))
            return

        self.send_json({'status': 'erro', 'msg': 'Rota nao encontrada'})

    def gerar_relatorio(self, nome):
        if company_has_report(nome):
            safe = re.sub(r'[\\/*?:"<>|]', '', nome[:50]).strip().replace(' ', '_')
            pdf_name = f"{safe}_relatorio.pdf"
            return {'status': 'existe', 'msg': 'Relatorio ja existe', 'pdf': f'relatorios/{pdf_name}'}

        company = find_company(nome)
        if not company:
            return {'status': 'erro', 'msg': 'Empresa nao encontrada no banco'}

        # Gera relatorio em background
        def gerar():
            try:
            report_text = generate_report(company)
            if report_text:
                    save_report_as_pdf(company, report_text)
                    reports_set = load_reports_log()
                    reports_set.add(company['name'])
                    save_reports_log(reports_set)
            except Exception as e:
                print(f"Erro ao gerar relatorio de {nome}: {e}", flush=True)

        t = threading.Thread(target=gerar, daemon=True)
        t.start()
        safe = re.sub(r'[\\/*?:"<>|]', '', nome[:50]).strip().replace(' ', '_')
        pdf_name = f"{safe}_relatorio.pdf"
        return {'status': 'gerando', 'msg': 'Relatorio esta sendo gerado (pode levar ate 1 minuto)', 'pdf': f'relatorios/{pdf_name}'}

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def translate_path(self, path):
        # Serve da pasta do projeto
        if path.startswith('/relatorios/'):
            return os.path.join(BASE_DIR, path.lstrip('/'))
        if path == '/' or path == '':
            return os.path.join(BASE_DIR, 'ranking_empresas.html')
        return os.path.join(BASE_DIR, path.lstrip('/'))

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]} {args[1]} {args[2]}", flush=True)

if __name__ == '__main__':
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(('localhost', PORT), RankingHandler)
    print(f"Servidor rodando em http://localhost:{PORT}")
    print("Pressione Ctrl+C para parar")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
