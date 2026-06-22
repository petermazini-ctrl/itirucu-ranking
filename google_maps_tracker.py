import os
import json
import re
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não encontrados no arquivo .env")
    exit()

REGION = "Itiruçu, Bahia"
RADIUS_KM = 60 # Não é usado diretamente na pesquisa do Google Maps, mas serve como referência
TRACKED_COMPANIES_FILE = os.path.join(os.path.dirname(__file__), "tracked_companies.json")

def escape_html(text):
    """Escapa caracteres especiais do HTML."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def send_telegram_message(message):
    """Envia uma mensagem para o Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Mensagem enviada com sucesso para o Telegram.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")
        return False

def load_tracked_companies():
    """Carrega as empresas já rastreadas do arquivo JSON."""
    if os.path.exists(TRACKED_COMPANIES_FILE):
        with open(TRACKED_COMPANIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tracked_companies(companies):
    """Salva as empresas rastreadas no arquivo JSON."""
    with open(TRACKED_COMPANIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(companies, f, indent=4, ensure_ascii=False)

def scrape_website_data(url, timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    result = {'email': '', 'social': []}
    social_patterns = [
        (r'(?:https?://)?(?:www\.)?instagram\.com/[a-zA-Z][a-zA-Z0-9_.]{2,}', 'Instagram'),
        (r'(?:https?://)?(?:www\.)?facebook\.com/[a-zA-Z0-9.]+', 'Facebook'),
        (r'(?:https?://)?(?:www\.)?linkedin\.com/company/[a-zA-Z0-9-]+', 'LinkedIn'),
        (r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+', 'LinkedIn'),
        (r'(?:https?://)?(?:www\.)?youtube\.com/@[a-zA-Z0-9_-]+', 'YouTube'),
        (r'(?:https?://)?(?:www\.)?youtube\.com/channel/[a-zA-Z0-9_-]+', 'YouTube'),
        (r'(?:https?://)?(?:www\.)?tiktok\.com/@?[a-zA-Z0-9_.]+', 'TikTok'),
        (r'(?:https?://)?(?:www\.)?twitter\.com/[a-zA-Z0-9_]+', 'Twitter'),
        (r'(?:https?://)?(?:www\.)?x\.com/[a-zA-Z0-9_]+', 'X'),
    ]
    exclude_urls = ['rsrc.php', 'intent', 'share.php', 'plugins/', 'sharer.php', '.png', '.jpg', '.gif', '.svg', '.css', '.js',
                    '/tr', '/v/', '/_u', '/embed', '/watch', 'sharer', 'plugins']
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            emails = re.findall(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}', resp.text)
            for e in emails:
                if not e.lower().endswith(('.png', '.jpg', '.gif', '.svg', '.css', '.js')):
                    result['email'] = e
                    break
            found = set()
            for pattern, name in social_patterns:
                matches = re.findall(pattern, resp.text, re.IGNORECASE)
                for m in matches:
                    url_clean = m if m.startswith('http') else f'https://{m}'
                    if url_clean not in found and not any(ex in url_clean for ex in exclude_urls):
                        found.add(url_clean)
                        result['social'].append({'name': name, 'url': url_clean})
    except:
        pass
    return result

def search_google_maps(term):
    """Faz uma busca no Google Maps e retorna empresas encontradas."""
    seen = set()
    results = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
            context = browser.new_context(locale='pt-BR', viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            url = f"https://www.google.com/maps/search/{term.replace(' ', '+')}"
            page.goto(url, timeout=30000, wait_until='domcontentloaded')
            time.sleep(4)
            feed = page.locator('div[role="feed"]')
            feed.first.wait_for(timeout=10000)
            for _ in range(40):
                feed.first.press("PageDown")
                time.sleep(0.4)
            data = page.evaluate("""() => {
                const articles = document.querySelectorAll('div[role="article"]');
                const results = [];
                articles.forEach(article => {
                    const name = article.getAttribute('aria-label') || '';
                    if (!name) return;
                    const text = article.innerText || '';
                    const lines = text.split('\\n').filter(l => l.trim());
                    const links = article.querySelectorAll('a');
                    let website = '';
                    for (const a of links) {
                        const href = a.getAttribute('href') || '';
                        if (href.startsWith('http') && !href.includes('google.com/maps')) { website = href; break; }
                    }
                    const phoneMatch = text.match(/(\\(\\d{2}\\)\\s*\\d{4,5}-?\\d{4})/);
                    const phone = phoneMatch ? phoneMatch[1] : '';
                    let place_id = '';
                    for (const a of links) {
                        const href = a.getAttribute('href') || '';
                        const pid = href.match(/!1s([a-f0-9:]+)/);
                        if (pid) { place_id = pid[1]; break; }
                    }
                    let category = '', address = '';
                    for (let i = 0; i < lines.length; i++) {
                        const line = lines[i].trim();
                        if (line.includes('·') && !line.includes('estrelas')) {
                            const parts = line.split('·').map(s => s.trim());
                            category = parts[0] || '';
                            if (parts.length > 1) address = parts.slice(1).join(' · ').trim();
                            break;
                        }
                    }
                    let rating = 0;
                    const ratingSpan = article.querySelector('span[role="img"]');
                    if (ratingSpan) {
                        const r = ratingSpan.getAttribute('aria-label') || '';
                        const rm = r.match(/([\\d,]+)\\s*estrelas/);
                        if (rm) rating = parseFloat(rm[1].replace(',', '.'));
                    }
                    let reviews = 0;
                    const ratingNumMatch = text.match(/(\\d+[.,]\\d+)\\s*\\((\\d+)\\)/);
                    if (ratingNumMatch) {
                        reviews = parseInt(ratingNumMatch[2]);
                    }
                    let hours = '';
                    const hourMatch = text.match(/(Aberto|Fechado)\\s*[^\\n]*/);
                    if (hourMatch) hours = hourMatch[0].trim();
                    let map_link = '';
                    for (const a of links) {
                        const href = a.getAttribute('href') || '';
                        if (href.includes('google.com/maps/place/') || href.startsWith('/maps/place/')) {
                            map_link = href.startsWith('http') ? href : 'https://www.google.com' + href;
                            break;
                        }
                    }
                    const emailMatch = text.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\\.[a-zA-Z]{2,})/);
                    const email = emailMatch ? emailMatch[1] : '';
                    results.push({ name, category, address, phone, website, email,
                        rating, reviews, hours, place_id, map_link });
                });
                return results;
            }""")
            EXCLUDE_KEYWORDS = ['bairro', 'distrito', 'terminal rodoviario', 'itirucu', 'itiruçu',
                'rua ', 'avenida', 'travessa', 'praça', 'praca', 'loteamento', 'povoado',
                'sítio', 'sitio', 'fazenda ', 'rota ', 'polícia', 'policia', 'banco ',
                'bradesco', 'caixa econômica', 'caixa economica', 'cartório', 'cartorio',
                'correios', 'igreja universal', 'testemunhas de jeová', 'testemunhas de jeova',
                'salão do reino']
            EXCLUDE_CATEGORIES = ['complexo habitacional', 'escritorio da empresa', 'escritório da empresa',
                'habitação', 'companhia de gás', 'companhia de gas', 'fechado',
                'rua', 'estrada', 'bairro', 'loteamento', 'povoado', 'sítio', 'sitio',
                'polícia', 'policia', 'banco', 'cartório', 'cartorio', 'correio',
                'igreja', 'templo religioso']
            for item in data:
                name = item.get("name", "N/A")
                if name in seen: continue
                cat = (item.get("category", "") or "").lower()
                if any(kw in name.lower() for kw in EXCLUDE_KEYWORDS): continue
                if any(kw in cat for kw in EXCLUDE_CATEGORIES): continue
                seen.add(name)
                results.append({"name": name, "category": item.get("category", "N/A"),
                    "address": item.get("address", "N/A"), "website": item.get("website", ""),
                    "phone": item.get("phone", ""), "email": item.get("email", ""), "social": [],
                    "rating": item.get("rating", 0), "reviews": item.get("reviews", 0),
                    "hours": item.get("hours", ""), "place_id": item.get("place_id", ""),
                    "map_link": item.get("map_link", ""),
                    "has_website": bool(item.get("website", ""))})
            browser.close()
    except Exception as e:
        print(f"    Erro: {e}", flush=True)
    return results

def get_companies_from_google_maps(region, tracked_companies=None):
    """Rastreia empresas no Google Maps para a região especificada."""
    import re
    all_data = []
    seen_names = set()

    def save_progress():
        if tracked_companies is not None:
            with open(TRACKED_COMPANIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(tracked_companies, f, indent=2, ensure_ascii=False)
            print(f"  (progresso salvo: {len(tracked_companies)} empresas)", flush=True)

    search_terms = [
        # Entroncamento de Jaguaquara - processado primeiro
        f"empresas em Entroncamento de Jaguaquara, Bahia",
        f"restaurantes lojas farmacias em Entroncamento de Jaguaquara",
        f"postos hoteis pousadas em Entroncamento de Jaguaquara",
        f"oficinas mercadinhos padarias em Entroncamento de Jaguaquara",
        f"servicos georreferenciamento topografia em Entroncamento de Jaguaquara",
        f"ti informatica mecanico eletricista em Entroncamento de Jaguaquara",
        f"manicure estetica buffet eventos em Entroncamento de Jaguaquara",
        f"seguranca limpeza transporte fretes em Entroncamento de Jaguaquara",
        f"borracharia mecanica oficina em Entroncamento de Jaguaquara",
        f"acougue refrigeracao assistencia tecnica em Entroncamento de Jaguaquara",
        f"lava jato funilaria pintura em Entroncamento de Jaguaquara",
        f"clinica otica farmacia manipulacao em Entroncamento de Jaguaquara",
        f"auto escola curso profissionalizante em Entroncamento de Jaguaquara",
        f"loja roupas calcados papelaria em Entroncamento de Jaguaquara",
        f"agropecuaria insumos cooperativa em Entroncamento de Jaguaquara",
        f"cameras seguranca cftv assistencia tecnica em Entroncamento de Jaguaquara",
        f"tatuagem dj decoracao festas em Entroncamento de Jaguaquara",
        f"construtora serralheria vidracaria em Entroncamento de Jaguaquara",
        f"marmoraria moveis planejados decoracao em Entroncamento de Jaguaquara",
        f"chaveiro despachante oficina em Entroncamento de Jaguaquara",
        f"hortifruti floricultura viveiro em Entroncamento de Jaguaquara",
        f"hotel pousada hospedagem em Entroncamento de Jaguaquara",
        f"comunicacao visual grafica em Entroncamento de Jaguaquara",
        f"banda dj som iluminacao em Entroncamento de Jaguaquara",
        f"internet provedor informatica em Entroncamento de Jaguaquara",
        f"mecanica caminhao auto center em Entroncamento de Jaguaquara",
        f"vidros aluminio esquadrias em Entroncamento de Jaguaquara",
        f"advocacia advogado em Entroncamento de Jaguaquara",
        # Jaguaquara
        f"empresas em Jaguaquara, Bahia",
        f"restaurantes lojas farmacias em Jaguaquara",
        f"postos hoteis pousadas em Jaguaquara",
        f"oficinas mercadinhos padarias em Jaguaquara",
        f"clinicas medicos dentistas em Jaguaquara",
        f"salão beleza barbearia estetica em Jaguaquara",
        f"material construcao ferragem em Jaguaquara",
        f"loja moveis decoracao em Jaguaquara",
        f"advocacia advogado em Jaguaquara",
        # Itiruçu
        f"empresas em {region}",
        f"restaurantes pizzarias padarias em {region}",
        f"clinicas consultorios dentistas em {region}",
        f"lojas mercados farmacias bares academias em {region}",
        f"postos de gasolina pousadas hoteis em {region}",
        f"advocacia corretores imoveis concessionarias em {region}",
        f"oficinas auto pecas borracharias em {region}",
        f"construcao material pintura eletrica em {region}",
        f"salão de beleza barbearia estetica em {region}",
        f"escolas cursos academia educacao em {region}",
        f"veterinario pet shop agro em {region}",
        f"igrejas templos centros religiosos em {region}",
        f"transporte taxi mototaxi fretes em {region}",
        f"seguros contabilidade consultoria em {region}",
        f"funeraria floricultura presentes em {region}",
        f"georreferenciamento topografia agrimensura em {region}",
        f"ti informatica suporte tecnico em {region}",
        f"manicure depilacao estetica avancada em {region}",
        f"mecanico eletricista encanador pintor pedreiro em {region}",
        f"seguranca vigilancia portaria em {region}",
        f"limpeza dedetizacao conservacao em {region}",
        f"fotografia filmagem drone em {region}",
        f"eventos buffet festas recreacao em {region}",
        f"costura alfaiataria moda em {region}",
        f"entregas frete mudancas logistica em {region}",
        f"engenharia arquitetura projeto em {region}",
        f"jardinagem paisagismo em {region}",
        f"serralheria solda esquadria em {region}",
        f"guincho reboque em {region}",
        f"hotelaria hospedagem pousada em {region}",
        f"borracharia pneu recapagem em {region}",
        f"mecanica auto center reparos em {region}",
        f"assistencia tecnica conserto reparo em {region}",
        f"acougue carne frigorifico em {region}",
        f"refrigeracao ar condicionado geladeira em {region}",
        f"despachante transferencia veiculo em {region}",
        f"lava jato lavagem carro em {region}",
        f"funilaria pintura automotiva em {region}",
        f"clinica medica medico especialista em {region}",
        f"fisioterapeuta terapia em {region}",
        f"psicologo psicologia psiquiatra em {region}",
        f"laboratorio analises clinicas em {region}",
        f"otica optometrista oculos em {region}",
        f"farmacia manipulacao em {region}",
        f"mercearia minimercado conveniencia em {region}",
        f"lanchonete sanduicheria lanche em {region}",
        f"peixaria frutos do mar em {region}",
        f"sucos acai sorveteria em {region}",
        f"auto escola formacao condutores em {region}",
        f"curso idiomas ingles em {region}",
        f"curso profissionalizante senac em {region}",
        f"reforco escolar ensino em {region}",
        f"dedetizadora desinsetizacao em {region}",
        f"chaveiro chaves automotivo em {region}",
        f"mudancas transporte cargas em {region}",
        f"loja roupas moda feminina masculina em {region}",
        f"loja calcados sapatos em {region}",
        f"loja utilidades domesticas em {region}",
        f"agropecuaria insumos racao em {region}",
        f"papelaria livraria material escolar em {region}",
        f"cooperativa agricola produtor em {region}",
        f"cameras seguranca cftv alarme em {region}",
        f"assistencia tecnica celular smartphone em {region}",
        f"tatuagem tatuador body piercing em {region}",
        f"dj som iluminacao festa em {region}",
        f"decoracao festas eventos em {region}",
        f"aluguel mesas cadeiras tendas em {region}",
        f"loja moveis decoracao em {region}",
        f"material construcao ferragem em {region}",
        f"loja bicicleta pecas em {region}",
        f"informatica notebook computador em {region}",
        f"casa festas brinquedos infantis em {region}",
        f"deposito bebidas distribuidora em {region}",
    ]

    for term in search_terms:
        print(f"  Buscando: {term}...", flush=True)
        batch = search_google_maps(term)
        for item in batch:
            if item['name'] not in seen_names:
                seen_names.add(item['name'])
                item['first_seen'] = datetime.now().isoformat()
                all_data.append(item)
        print(f"    +{len(batch)} encontradas ({len(seen_names)} unicas)", flush=True)
        time.sleep(2)
        # Salva progresso a cada 5 buscas
        if len(all_data) > 0 and len(all_data) % 10 < 5:
            temp_file = os.path.join(os.path.dirname(__file__), "_temp_search.json")
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
        if len(all_data) > 0 and len(all_data) % 10 == 0:
            save_progress()

    return all_data

def main():
    print(f"Iniciando rastreamento de empresas em {REGION}...")
    tracked_companies = load_tracked_companies()
    
    current_companies = get_companies_from_google_maps(REGION, tracked_companies)
    print(f"Encontradas {len(current_companies)} empresas no Google Maps na busca atual.", flush=True)

    # Tenta extrair email e redes sociais do site (max 10 sites)
    site_count = 0
    for c in current_companies:
        if c.get('website') and site_count < 10:
            print(f"  Buscando dados no site de {c['name']}...")
            data = scrape_website_data(c['website'], timeout=8)
            if data['email'] and not c.get('email'):
                c['email'] = data['email']
                print(f"    Email: {data['email']}")
            if data['social']:
                c['social'] = data['social']
                for s in data['social']:
                    print(f"    {s['name']}: {s['url']}")
            site_count += 1
            time.sleep(0.5)

    new_companies_found = []
    for company in current_companies:
        matched = False
        for tracked in tracked_companies:
            if tracked['name'] == company['name'] and tracked['address'] == company['address']:
                matched = True
                # Atualiza dados da busca atual (sempre sobrescreve)
                tracked['rating'] = company.get('rating', 0)
                tracked['reviews'] = company.get('reviews', 0)
                tracked['phone'] = company.get('phone', tracked.get('phone', ''))
                tracked['website'] = company.get('website', tracked.get('website', ''))
                tracked['hours'] = company.get('hours', tracked.get('hours', ''))
                tracked['map_link'] = company.get('map_link', tracked.get('map_link', ''))
                if company.get('email') and not tracked.get('email'):
                    tracked['email'] = company['email']
                    print(f"  Email atualizado para {tracked['name']}: {company['email']}")
                if company.get('social') and not tracked.get('social'):
                    tracked['social'] = company['social']
                    print(f"  Redes sociais atualizadas para {tracked['name']}")
                break
        
        if not matched:
            new_companies_found.append(company)
            tracked_companies.append(company) 

    if new_companies_found:
        # Salva antes dos alertas Telegram (evita perder dados se timeout)
        save_tracked_companies(tracked_companies)
        print(f"Progresso salvo antes dos alertas Telegram.", flush=True)
        
        print(f"Novas empresas identificadas: {len(new_companies_found)}")
        for i, company in enumerate(new_companies_found):
            social_text = ""
            if company.get('social'):
                social_text = "\n<b>Redes Sociais:</b>\n"
                for s in company['social'][:3]:
                    social_text += f"  {s['name']}: {escape_html(s['url'])}\n"

            message = f"""🚨 <b>Nova Empresa na sua Região ({escape_html(REGION)})!</b> 🚨

<b>Nome:</b> {escape_html(company['name'])}
<b>Categoria:</b> {escape_html(company['category'])}
<b>Endereço:</b> {escape_html(company['address'])}
<b>Site:</b> {escape_html(company['website'])}
<b>Telefone:</b> {escape_html(company['phone'])}
<b>Email:</b> {escape_html(company.get('email', 'N/A'))}
<b>Avaliação:</b> {company.get('rating', '?')}⭐ ({company.get('reviews', 0)} reviews)
{social_text}
---"""
            send_telegram_message(message)
            # Delay entre mensagens para evitar rate limiting
            if i < len(new_companies_found) - 1:
                time.sleep(2)
    else:
        print("Nenhuma nova empresa encontrada neste ciclo de rastreamento.")

    save_tracked_companies(tracked_companies)
    print(f"Lista de empresas rastreadas atualizada em '{TRACKED_COMPANIES_FILE}'.")

if __name__ == "__main__":
    main()
