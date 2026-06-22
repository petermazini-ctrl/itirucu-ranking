import os
import re
import json
import time
import requests
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF
import qrcode

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TRACKED_FILE = os.path.join(os.path.dirname(__file__), 'tracked_companies.json')
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'relatorios')
REPORT_LOG_FILE = os.path.join(os.path.dirname(__file__), 'reports_generated.json')
MAX_PER_RUN = 5

os.makedirs(REPORTS_DIR, exist_ok=True)

# Info de contato do usuario
CONTATO_NOME = "Piter Mazini Mota"
CONTATO_TEL = "73 98814-0990"
CONTATO_WA = "5573988140990"
CONTATO_EMAIL = "Pitemazini@gmail.com"
CONTATO_SERVICOS = "SEO, Gestao de Trafego, Criacao de sites, apps, automacao comercial, suporte TI, redes"
CONTATO_MSG = "Ola, Gostaria de saber mais sobre seus servicos"

def strip_markdown(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    return text

def escape_html(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def send_telegram_document(file_path, caption=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    with open(file_path, 'rb') as f:
        files = {'document': (os.path.basename(file_path), f, 'application/pdf')}
        data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
        requests.post(url, data=data, files=files, timeout=30)

def call_llm(prompt):
    providers = [
        {"name": "Mistral", "key": os.getenv('MISTRAL_API_KEY'), "url": "https://api.mistral.ai/v1/chat/completions", "model": "mistral-tiny"},
        {"name": "Groq", "key": os.getenv('GROQ_API_KEY'), "url": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.1-8b-instant"},
    ]

    for pv in providers:
        if not pv["key"]:
            continue
        headers = {"Authorization": f"Bearer {pv['key']}", "Content-Type": "application/json"}
        headers.update(pv.get("headers", {}))
        payload = {
            "model": pv["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        for tentativa in range(3):
            try:
                resp = requests.post(pv["url"], headers=headers, json=payload, timeout=120)
                if resp.status_code == 429:
                    print(f"  Rate limit {pv['name']}, aguardando...")
                    time.sleep(10)
                    continue
                resp.raise_for_status()
                return resp.json()['choices'][0]['message']['content']
            except Exception as e:
                print(f"  {pv['name']} tentativa {tentativa+1}/3: {e}")
                time.sleep(5)
    return None

def generate_report(company):
    nome = company['name']
    cat = company.get('category', 'N/A')
    end = company.get('address', 'N/A')
    site = company.get('website', 'N/A')
    tel = company.get('phone', 'N/A')
    rating = company.get('rating', 0)
    reviews = company.get('reviews', 0)
    has_site = company.get('has_website', False)
    first_seen = company.get('first_seen', datetime.now().isoformat())
    try:
        data_detect = datetime.fromisoformat(first_seen).strftime('%d/%m/%Y')
    except:
        data_detect = datetime.now().strftime('%d/%m/%Y')

    social_data = company.get('social', [])
    social_text = ""
    if social_data:
        social_text = "Redes Sociais:\n" + "\n".join([f"  {s['name']}: {s['url']}" for s in social_data])

    prompt = f"""Gere um relatorio de marketing digital para a empresa abaixo. NAO use marcacao markdown (** ou * ou []). Use apenas texto simples com paragrafos e topicos com -.

Empresa: {nome}
Categoria: {cat}
Endereco: {end}
Site: {site}
Telefone: {tel}
Email: {company.get('email', 'N/A')}
Avaliacao: {rating} estrelas ({reviews} reviews)
Possui site: {"Sim" if has_site else "Nao"}
Data de deteccao: {data_detect}
{social_text}

Estrutura obrigatoria:
1. ANALISE DE PRESENCA DIGITAL - Como a empresa esta no Google Maps, site e redes sociais. Considere a nota {rating} e {reviews} reviews.
2. RECOMENDACOES SEO - Melhorias para Google Meu Negocio e SEO local
3. PROPOSTA DE SERVICOS - O que oferecemos (site, Google Ads, conteudo)
4. PLANO DE ACAO 30 DIAS - 5 passos concretos"""
    return call_llm(prompt)

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, 'Relatorio de Marketing Digital & SEO', new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')

def sanitize(text):
    return ''.join(c for c in text if ord(c) < 256)

def save_report_as_pdf(company, report_text):
    nome = sanitize(company['name'])[:50]
    safe_name = re.sub(r'[\\/*?:"<>|]', '', nome).strip().replace(' ', '_')
    filepath = os.path.join(REPORTS_DIR, f"{safe_name}_relatorio.pdf")

    first_seen = company.get('first_seen', datetime.now().isoformat())
    try:
        data_detect = datetime.fromisoformat(first_seen).strftime('%d/%m/%Y')
    except:
        data_detect = datetime.now().strftime('%d/%m/%Y')
    data_hoje = datetime.now().strftime('%d/%m/%Y %H:%M')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Titulo
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 16, f"Relatorio: {nome}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', 'I', 16)
    pdf.set_text_color(108, 117, 125)
    pdf.cell(0, 9, f"Gerado em {data_hoje}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 9, f"Empresa detectada em: {data_detect}", new_x="LMARGIN", new_y="NEXT")
    rating = company.get('rating', 0)
    reviews = company.get('reviews', 0)
    has_site = company.get('has_website', False)
    if rating:
        pdf.cell(0, 9, f"Avaliacao: {rating} estrelas ({reviews} reviews) | Possui site: {'Sim' if has_site else 'Nao'}", new_x="LMARGIN", new_y="NEXT")
    # Dados de contato do cliente
    client_tel = company.get('phone', '')
    client_email = company.get('email', '')
    client_site = company.get('website', '')
    if client_tel:
        pdf.set_font('Helvetica', '', 16)
        tel_clean = re.sub(r'[^\d]', '', client_tel)
        wa_link = f"https://wa.me/55{tel_clean}?text={requests.utils.quote('Ola, vi seu relatorio de marketing digital')}"
        pdf.set_text_color(37, 211, 102)
        pdf.cell(0, 9, f"{client_tel}", new_x="LMARGIN", new_y="NEXT", link=wa_link)
    if client_email:
        pdf.set_font('Helvetica', '', 16)
        pdf.set_text_color(43, 108, 176)
        pdf.cell(0, 9, f"Email: {client_email}", new_x="LMARGIN", new_y="NEXT", link=f"mailto:{client_email}")
    if client_site and client_site != 'N/A':
        pdf.set_font('Helvetica', '', 16)
        pdf.set_text_color(43, 108, 176)
        pdf.cell(0, 9, f"Site: {client_site}", new_x="LMARGIN", new_y="NEXT", link=client_site)
    # Redes sociais
    social_data = company.get('social', [])
    for s in social_data[:4]:
        pdf.set_font('Helvetica', '', 15)
        pdf.set_text_color(43, 108, 176)
        pdf.cell(0, 8, f"{s['name']}: {s['url']}", new_x="LMARGIN", new_y="NEXT", link=s['url'])
    if not client_tel and not client_email and not social_data:
        pdf.set_font('Helvetica', 'I', 14)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 9, "Sem contato disponivel", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Conteudo
    pdf.set_text_color(33, 37, 41)
    texto_limpo = strip_markdown(report_text)
    linhas = sanitize(texto_limpo).split('\n')

    for linha in linhas:
        ls = linha.strip()
        if not ls:
            pdf.ln(2)
            continue
        if any(ls.upper().startswith(p) for p in ['1.', '2.', '3.', '4.', '5.', '6.']):
            pdf.set_font('Helvetica', 'B', 17)
            pdf.ln(4)
            pdf.multi_cell(0, 9, ls, new_x="LMARGIN", new_y="NEXT")
        elif ls.startswith('- '):
            pdf.set_font('Helvetica', '', 16)
            pdf.multi_cell(0, 8, "  " + ls[2:], new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font('Helvetica', '', 16)
            pdf.multi_cell(0, 8, ls, new_x="LMARGIN", new_y="NEXT")

    # Linha divisoria
    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    y_line = pdf.get_y()
    pdf.line(pdf.l_margin, y_line, pdf.w - pdf.r_margin, y_line)
    pdf.ln(6)

    # QR Code do WhatsApp
    wa_url = f"https://wa.me/{CONTATO_WA}?text={requests.utils.quote(CONTATO_MSG)}"
    qr = qrcode.make(wa_url)
    qr_path = os.path.join(tempfile.gettempdir(), "wa_qr.png")
    qr.save(qr_path)

    # Posicao do QR code no canto direito
    qr_size = 35
    qr_x = pdf.w - pdf.r_margin - qr_size
    qr_y = pdf.get_y()
    pdf.image(qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)

    # Texto de contato ao lado esquerdo
    pdf.set_xy(pdf.l_margin, qr_y)
    pdf.set_font('Helvetica', 'B', 17)
    pdf.set_text_color(43, 108, 176)
    pdf.cell(0, 10, "Fale Conosco", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 16)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 9, f"{CONTATO_NOME}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 9, f"Telefone: {CONTATO_TEL}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 9, f"Email: {CONTATO_EMAIL}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', 'I', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 8, f"Servicos: {CONTATO_SERVICOS}", new_x="LMARGIN", new_y="NEXT")

    # Link clickavel do WhatsApp
    pdf.ln(2)
    link_y = pdf.get_y()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(37, 211, 102)
    pdf.cell(0, 9, "Clique aqui para falar conosco pelo WhatsApp", new_x="LMARGIN", new_y="NEXT", link=wa_url)
    # Destaca o QR code com link tambem
    pdf.link(qr_x, qr_y, qr_size, qr_size, wa_url)

    pdf.ln(4)
    os.remove(qr_path)

    pdf.output(filepath)
    return filepath

def main():
    if not os.path.exists(TRACKED_FILE):
        print("tracked_companies.json nao encontrado.")
        return

    with open(TRACKED_FILE, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    if os.path.exists(REPORT_LOG_FILE):
        with open(REPORT_LOG_FILE, 'r', encoding='utf-8') as f:
            already = json.load(f)
    else:
        already = []

    pendentes = [c for c in companies if c['name'] not in already][:MAX_PER_RUN]

    if not pendentes:
        print("Nenhuma empresa pendente.")
        return

    print(f"Gerando ate {len(pendentes)} relatorios...")
    send_telegram_message(f"Iniciando geracao de {len(pendentes)} relatorios...")

    for i, company in enumerate(pendentes):
        nome = company['name']
        print(f"[{i+1}/{len(pendentes)}] {nome.encode('latin-1', errors='replace').decode('latin-1')}...")

        report = generate_report(company)
        if not report:
            print(f"  Falha apos tentativas")
            continue

        filepath = save_report_as_pdf(company, report)
        print(f"  PDF: {filepath}")

        try:
            send_telegram_document(filepath, f"Relatorio: <b>{escape_html(nome)}</b> | {company.get('rating', '?')} estrelas")
        except:
            print(f"  Falha ao enviar PDF via Telegram")
        already.append(nome)

        with open(REPORT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(already, f, indent=2, ensure_ascii=False)

        time.sleep(5)

    print("Concluido.")

if __name__ == "__main__":
    main()
