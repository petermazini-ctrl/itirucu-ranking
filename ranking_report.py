import json
import os
from collections import defaultdict

TRACKED_FILE = os.path.join(os.path.dirname(__file__), "tracked_companies.json")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "ranking_empresas.html")

with open(TRACKED_FILE, encoding='utf-8') as f:
    companies = json.load(f)

# Filtra empresas de Jequié (foco é Itiruçu e Entroncamento de Jaguaquara)
JEQUIE_KEYWORDS = ['jequié', 'jequie', 'jequitibá']
def is_jequie(c):
    name = (c.get('name', '') or '').lower()
    addr = (c.get('address', '') or '').lower()
    cat = (c.get('category', '') or '').lower()
    return any(kw in name or kw in addr or kw in cat for kw in JEQUIE_KEYWORDS)

companies = [c for c in companies if not is_jequie(c)]

# Normaliza categorias (agrupa sinonimos)
CATEGORY_MAP = {
    'advogado': 'Advocacia',
    'advogado previdenciário': 'Advocacia',
    'advogado criminal': 'Advocacia',
    'advogado de práticas gerais': 'Advocacia',
    'advogado contencioso': 'Advocacia',
    'advogado administrativo': 'Advocacia',
    'advogado especialista em divórcios': 'Advocacia',
    'advogado de direito de família': 'Advocacia',
    'advogado(a) civil': 'Advocacia',
    'advogado trabalhista': 'Advocacia',
    'serviços jurídicos': 'Advocacia',
    'assistência jurídica': 'Advocacia',
    'escritório de advocacia': 'Advocacia',
    'oficina mecânica': 'Oficina Mecânica / Auto Peças',
    'mecânica para carros': 'Oficina Mecânica / Auto Peças',
    'loja de autopeças': 'Oficina Mecânica / Auto Peças',
    'oficina de caminhões': 'Oficina Mecânica / Auto Peças',
    'mecânica': 'Oficina Mecânica / Auto Peças',
    'comércio de pneu': 'Oficina Mecânica / Auto Peças',
    'loja de acessórios para caminhões': 'Oficina Mecânica / Auto Peças',
    'borracharia': 'Oficina Mecânica / Auto Peças',
    'loja de pneus usados': 'Oficina Mecânica / Auto Peças',
    'loja de radiadores': 'Oficina Mecânica / Auto Peças',
    'funilaria': 'Funilaria / Pintura',
    'lava-rápido': 'Lava Jato / Estética Automotiva',
    'açougue': 'Açougue',
    'açougue / frigorífico': 'Açougue',
    'clínica odontológica': 'Clínicas / Dentistas',
    'dentista': 'Clínicas / Dentistas',
    'odontopediatra': 'Clínicas / Dentistas',
    'supermercado': 'Mercados / Supermercados',
    'mercearia': 'Mercados / Supermercados',
    'peixaria': 'Peixaria / Frutos do Mar',
    'escola de idiomas': 'Escolas / Cursos / Educação',
    'escola de inglês': 'Escolas / Cursos / Educação',
    'escola de educação geral': 'Escolas / Cursos / Educação',
    'instituição educacional': 'Escolas / Cursos / Educação',
    'centro educacional': 'Escolas / Cursos / Educação',
    'centro escolar': 'Escolas / Cursos / Educação',
    'aulas particulares': 'Escolas / Cursos / Educação',
    'ensino fundamental': 'Escolas / Cursos / Educação',
    'jardim de infância': 'Escolas / Cursos / Educação',
    'escola pública': 'Escolas / Cursos / Educação',
    'autoescola': 'Auto Escola',
    'hotel / pousada / hospedagem': 'Hotéis / Pousadas',
    'hospedagem domiciliar': 'Hotéis / Pousadas',
    'farmacia': 'Farmácias / Drogarias',
    'drogaria': 'Farmácias / Drogarias',
    'restaurante italiano': 'Restaurantes',
    'restaurante': 'Restaurantes',
    'hamburgueria': 'Lanchonetes / Hamburguerias',
    'lanchonete': 'Lanchonetes / Hamburguerias',
    'churrascaria': 'Restaurantes',
    'sorveteria': 'Sorveterias / Açaí',
    'marmoraria': 'Marmoraria / Mármore / Granito',
    'construtora': 'Construção / Reformas',
    'empreiteira de serviços com gesso': 'Construção / Reformas',
    'prestador de serviços de construção civil': 'Construção / Reformas',
    'material de construção / ferragem': 'Material de Construção',
    'loja de materiais de construção': 'Material de Construção',
    'loja de ferragens': 'Material de Construção',
    'loja de tintas': 'Material de Construção',
    'loja de madeiras': 'Material de Construção',
    'loja de artigos para reforma': 'Material de Construção',
    'loja de artigos domésticos': 'Material de Construção / Utilidades',
    'loja de utensílios de cozinha': 'Material de Construção / Utilidades',
    'loja de eletrodomésticos': 'Eletrodomésticos / Eletrônicos',
    'loja de eletrônicos': 'Eletrodomésticos / Eletrônicos',
    'loja de Informática': 'Informática / TI',
    'serviço de informática': 'Informática / TI',
    'operadora de internet': 'Informática / TI',
    'empresa de Software': 'Informática / TI',
    'loja de celulares': 'Informática / TI',
    'loja de móveis': 'Móveis / Decoração',
    'moveleiro': 'Móveis / Decoração',
    'fornecedor de móveis planejados': 'Móveis / Decoração',
    'loja de móveis para cozinha': 'Móveis / Decoração',
    'marcenaria': 'Móveis / Decoração',
    'marceneiro': 'Móveis / Decoração',
    'loja de colchões': 'Móveis / Decoração',
    'designer de interiores': 'Móveis / Decoração',
    'decorador de interiores': 'Móveis / Decoração',
    'estúdio de tatuagem e colocação de piercing': 'Tatuagem / Piercing',
    'estúdio de tatuagem': 'Tatuagem / Piercing',
    'loja de body piercing': 'Tatuagem / Piercing',
    'salão de Beleza': 'Salão de Beleza / Barbearia',
    'barbearia': 'Salão de Beleza / Barbearia',
    'cabeleireiro': 'Salão de Beleza / Barbearia',
    'spa facial': 'Salão de Beleza / Barbearia',
    'esteticista': 'Salão de Beleza / Barbearia',
    'centro de saúde e beleza': 'Salão de Beleza / Barbearia',
    'fabricante': 'Indústria / Fabricantes',
    'fabricante de alimentos congelados': 'Indústria / Fabricantes',
    'fabricante de alojamento móvel': 'Indústria / Fabricantes',
    'fabricação de alimentos': 'Indústria / Fabricantes',
    'metalúrgica': 'Indústria / Fabricantes',
    'serralharia': 'Serralheria / Solda / Esquadrias',
    'vidraçaria': 'Vidraçaria / Vidros',
    'serviço de conserto de vidros': 'Vidraçaria / Vidros',
    'tapeçaria': 'Tapeçaria / Estofaria',
    'serviço de reboque': 'Guincho / Reboque',
    'dedetizadora': 'Dedetizadora / Desinsetização',
    'fornecedor de gás butano': 'Gás / Distribuidora',
    'fornecedor de bebidas': 'Bebidas / Distribuidora',
    'agropecuária': 'Agropecuária / Insumos',
    'agricultura e pecuária': 'Agropecuária / Insumos',
    'fornecedor de feno': 'Agropecuária / Insumos',
    'atacadista de hortifrutigranjeiros': 'Hortifrúti / Horto',
    'floricultura': 'Hortifrúti / Horto',
    'floricultura atacadista': 'Hortifrúti / Horto',
    'fornecedor de produtos de limpeza': 'Produtos de Limpeza / Conservação',
    'serviço de distribuição': 'Logística / Distribuição',
    'empresa de transporte rodoviário': 'Logística / Distribuição',
    'serviço de transporte': 'Logística / Distribuição',
    'transporte / mudanças / logística': 'Logística / Distribuição',
    'táxi': 'Táxi / Transporte',
    'ponto de táxi': 'Táxi / Transporte',
    'agência de viagens': 'Agência de Viagens / Turismo',
    'loja de comunicaçao visual em vinil': 'Gráfica / Comunicação Visual',
    'gráfica': 'Gráfica / Comunicação Visual',
    'loja de camisetas personalizadas': 'Gráfica / Comunicação Visual',
    'papelaria': 'Papelaria / Livraria',
    'loja de produtos de papelaria': 'Papelaria / Livraria',
    'loja de presentes': 'Presentes / Variedades',
    'loja de variedades': 'Presentes / Variedades',
    'fotógrafo aéreo': 'Fotografia / Filmagem / Drone',
    'serviço de fotografia': 'Fotografia / Filmagem / Drone',
    'estúdio fotográfico': 'Fotografia / Filmagem / Drone',
    'produtor musical': 'Música / DJ / Áudio',
    'estação de rádio': 'Música / DJ / Áudio',
    'banda': 'Música / DJ / Áudio',
    'dj': 'Música / DJ / Áudio',
    'fornecedor de brindes': 'Brindes / Promocionais',
    'atacadista de roupas': 'Roupas / Moda',
    'loja de roupa': 'Roupas / Moda',
    'loja de calçado': 'Calçados',
    'loja de tecidos': 'Tecidos / Aviamentos',
    'escritório de contabilidade': 'Contabilidade / Consultoria',
    'serviço de segurança': 'Segurança / Vigilância',
    'centro médico': 'Clínicas / Médicos',
    'clínica especializada': 'Clínicas / Médicos',
    'hospital': 'Clínicas / Médicos',
    'saúde e segurança ocupacional': 'Clínicas / Médicos',
    'local para eventos': 'Eventos / Buffet / Festas',
    'salão de eventos': 'Eventos / Buffet / Festas',
    'salão de festas': 'Eventos / Buffet / Festas',
    'buffet infantil': 'Eventos / Buffet / Festas',
    'doceria': 'Doceria / Confeitaria',
    'confeitaria': 'Doceria / Confeitaria',
    'padaria': 'Padaria / Confeitaria',
    'fórum': 'Repartições Públicas',
    'repartição pública': 'Repartições Públicas',
    'repartição pública local': 'Repartições Públicas',
    'prefeitura': 'Repartições Públicas',
    'igreja': 'Igrejas / Templos',
    'igreja católica': 'Igrejas / Templos',
    'templo': 'Igrejas / Templos',
    'pet shop': 'Pet Shop / Veterinário',
    'empresa farmacêutica': 'Farmácias / Drogarias',
    'loja de bicicleta': 'Bicicletas / Peças',
    'concessionária Volvo': 'Concessionárias',
    'agência de marketing digital': 'Marketing / Publicidade',
    'designer gráfico': 'Marketing / Publicidade',
    'café': 'Café / Lanchonete',
    'mercado': 'Mercados / Supermercados',
    'mercado de frutas e vegetais': 'Mercados / Supermercados',
    'mercado de produtos agrícolas': 'Mercados / Supermercados',
    'verdureiro': 'Mercados / Supermercados',
    'armazém': 'Mercados / Supermercados',
    'atacadista': 'Atacadista / Distribuidora',
    'carpintaria': 'Carpintaria / Marcenaria',
    'chaveiro(a)': 'Chaveiro',
    'serviço de chaveiro emergencial': 'Chaveiro',
    'eletricista': 'Eletricista / Elétrica',
    'empresa de embalagens': 'Embalagens',
    'fazenda': 'Fazenda / Sítio',
    'ferreiro': 'Ferreiro / Serralheria',
    'fornecedor de produtos alimentícios': 'Alimentícios / Distribuidora',
    'garagem': 'Garagem / Estacionamento',
    'jardim': 'Jardinagem / Paisagismo',
    'loja': 'Lojas / Variedades',
    'loja de artigos para cama, mesa e banho': 'Cama, Mesa e Banho',
    'loja de bebidas alcoólicas': 'Bebidas / Distribuidora',
    'loja de bonecas': 'Lojas / Variedades',
    'loja de informática': 'Informática / TI',
    'loja de máquinas de lavar e secadoras': 'Eletrodomésticos / Eletrônicos',
    'loja de suprimentos agrícolas': 'Agropecuária / Insumos',
    'loja de vitaminas e suplementos': 'Farmácias / Drogarias',
    'lounge bar': 'Bares / Lounge',
    'pizzaria': 'Pizzarias',
    'posto de combustível': 'Posto de Combustível',
    'serviço de borracharia': 'Oficina Mecânica / Auto Peças',
    'serviço de conserto de motor a diesel': 'Oficina Mecânica / Auto Peças',
    'tornearia': 'Tornearia / Usinagem',
    'torrefação de café': 'Torrefação / Café',
    'ótica': 'Ótica',
    'farmácia': 'Farmácias / Drogarias',
    'salão de beleza': 'Salão de Beleza / Barbearia',
    'loja de marcenaria': 'Móveis / Decoração',
    'loja de comunicação visual em vinil': 'Gráfica / Comunicação Visual',
    # Categorias do Google Maps que precisam de mapeamento
    'banho e tosa': 'Pet Shop / Veterinário',
    'hospital geral': 'Clínicas / Médicos',
    'maternidade': 'Clínicas / Médicos',
    'pastelaria brasileira': 'Lanchonetes / Hamburguerias',
    'bar': 'Bares / Lounge',
    'bar de cervejas': 'Bares / Lounge',
    'diner': 'Lanchonetes / Hamburguerias',
    'espresso bar': 'Café / Lanchonete',
    'distribuidor de bebidas': 'Bebidas / Distribuidora',
    'restaurante japonês': 'Restaurantes',
    'agência de viagens de ônibus': 'Agência de Viagens / Turismo',
    'posto de abastecimento de veículos elétricos': 'Posto de Combustível',
    'loja de peças para motocicletas': 'Oficina Mecânica / Auto Peças',
    'revendedora de carros usados': 'Revendedora de Veículos',
    'serviço de contabilidade de custos': 'Contabilidade / Consultoria',
    'corretora de aluguel de imóveis': 'Imobiliária',
    'agente imobiliário': 'Imobiliária',
    'veterinário': 'Pet Shop / Veterinário',
    'assessoria contábil': 'Contabilidade / Consultoria',
    'concessionária volvo': 'Concessionárias',
}

for c in companies:
    cat = (c.get('category') or 'Sem categoria').strip().lower()
    if cat in CATEGORY_MAP:
        c['category'] = CATEGORY_MAP[cat]

# Filtra nichos invalidos (aberto, fechado, etc)
INVALID_CATEGORIES = {'aberto', 'aberto 24 horas', 'aberto agora', 'fechado', 'aberto agora', 'fecha em breve'}
for c in companies:
    cat = (c.get('category') or 'Sem categoria').strip().lower()
    if cat in INVALID_CATEGORIES:
        c['category'] = 'Sem categoria'

# Agrupa por categoria (cada empresa aparece uma unica vez)
nichos = defaultdict(list)
seen_in_cat = set()
for c in companies:
    nome = c.get('name', c.get('nome', ''))
    if nome in seen_in_cat:
        continue
    cat = c.get('category', 'Sem categoria') or 'Sem categoria'
    nichos[cat].append(c)
    seen_in_cat.add(nome)

# Ordena cada nicho: maior rating primeiro, depois por ter site como desempate
for cat in nichos:
    nichos[cat].sort(key=lambda c: (
        -(c.get('rating') or 0),
        -bool(c.get('website')),
        -bool(c.get('social'))
    ))

html = []
html.append("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ranking de Empresas por Nicho - Itiru\u00e7u & Entroncamento</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #333; padding: 12px; }
h1 { text-align: center; color: #1a73e8; margin-bottom: 5px; font-size: 20px; }
.subtitle { text-align: center; color: #666; margin-bottom: 20px; font-size: 13px; }
.nicho { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; overflow: hidden; }
.nicho-header { background: linear-gradient(135deg, #1a73e8, #0d47a1); color: #fff; padding: 12px 16px; font-size: 16px; font-weight: bold; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.nicho-header .count { background: rgba(255,255,255,0.2); padding: 2px 10px; border-radius: 20px; font-size: 12px; }
.table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; min-width: 600px; border-collapse: collapse; }
th { background: #f8f9fa; color: #555; font-size: 11px; text-transform: uppercase; padding: 8px; text-align: left; border-bottom: 2px solid #e0e0e0; white-space: nowrap; }
td { padding: 8px; border-bottom: 1px solid #f0f0f0; font-size: 12px; vertical-align: middle; }
tr:hover { background: #f5f8ff; }
tr.oportunidade { background: #fff8e1; }
tr.oportunidade:hover { background: #fff3cd; }
.rating { color: #f9a825; font-weight: bold; white-space: nowrap; }
.phone a { color: #25d366; text-decoration: none; font-weight: bold; font-size: 13px; white-space: nowrap; }
.social a { display: inline-block; margin: 2px 2px; font-size: 10px; padding: 3px 8px; border-radius: 4px; text-decoration: none; color: #fff; white-space: nowrap; }
.social .ig { background: #e1306c; }
.social .fb { background: #1877f2; }
.social .yt { background: #ff0000; }
.social .tt { background: #000; }
.social .in { background: #0a66c2; }
.social .tw { background: #1da1f2; }
.social .site { background: #666; }
.map-link a { color: #1a73e8; text-decoration: none; font-size: 11px; white-space: nowrap; }
.map-link a:hover { text-decoration: underline; }
.badge-oportunidade { display: inline-block; background: #ff6f00; color: #fff; font-size: 9px; padding: 1px 6px; border-radius: 8px; font-weight: bold; vertical-align: middle; }
.btn-relatorio { background: #1a73e8; color: #fff; border: none; border-radius: 4px; padding: 4px 10px; font-size: 11px; cursor: pointer; white-space: nowrap; transition: background 0.2s; }
.btn-relatorio:hover { background: #0d47a1; }
.btn-relatorio:disabled { background: #999; cursor: wait; }
.btn-relatorio-existe { display: inline-block; background: #34a853; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; text-decoration: none; white-space: nowrap; font-weight: bold; }
.btn-relatorio-existe:hover { background: #2d8f47; }
.relatorio { text-align: center; white-space: nowrap; }
#toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #333; color: #fff; padding: 10px 20px; border-radius: 8px; font-size: 13px; z-index: 999; display: none; max-width: 80%; text-align: center; }
.footer { text-align: center; color: #999; margin-top: 24px; font-size: 11px; }
.search-box { position: relative; max-width: 400px; margin: 0 auto 16px; }
.search-box input { width: 100%; padding: 10px 14px 10px 36px; border: 2px solid #ddd; border-radius: 24px; font-size: 14px; outline: none; transition: border-color 0.2s; }
.search-box input:focus { border-color: #1a73e8; }
.search-box .search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 16px; opacity: 0.5; }
.contact-bar { background: linear-gradient(135deg, #25d366, #128C7E); color: #fff; text-align: center; padding: 10px; border-radius: 12px; margin-bottom: 16px; font-size: 13px; }
.contact-bar a { color: #fff; font-weight: bold; text-decoration: none; }
.contact-bar a:hover { text-decoration: underline; }
.contact-bar small { opacity: 0.9; }
@media (max-width: 480px) {
  body { padding: 8px; }
  h1 { font-size: 17px; }
  .nicho-header { font-size: 14px; padding: 10px 12px; }
  td { font-size: 11px; padding: 6px; }
  .phone a { font-size: 12px; }
}
</style>
</head>
<body>
<h1>Ranking de Empresas por Nicho</h1>
<p class="subtitle">Itiru\u00e7u, Bahia &amp; Entroncamento de Jaguaquara</p>

<div class="search-box">
  <input type="text" id="searchInput" placeholder="Digite o nome da empresa ou segmento..." oninput="filtrar()">
  <span class="search-icon">&#128269;</span>
</div>
<p class="subtitle" id="contador"></p>

<div class="contact-bar">
  <strong>Piter Mazini Mota</strong> &mdash;
  <a href="https://wa.me/5573988140990" target="_blank">73 98814-0990</a> &mdash;
  <a href="mailto:Pitemazini@gmail.com">Pitemazini@gmail.com</a>
  <br><small>SEO, Gest&atilde;o de Tr&aacute;fego, Sites, Automa&ccedil;&atilde;o, Suporte TI, Redes</small>
</div>

<script>
var todosNichos = [];

function toggleTabela(header) {
  var tabela = header.nextElementSibling;
  if (tabela) tabela.style.display = tabela.style.display === 'none' ? 'block' : 'none';
}

function filtrar() {
  var termo = document.getElementById('searchInput').value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
  var totalVisiveis = 0;
  var divs = document.querySelectorAll('.nicho');
  divs.forEach(function(div) {
    var linhas = div.querySelectorAll('tbody tr');
    var algumVisivel = false;
    linhas.forEach(function(tr) {
      var texto = tr.textContent.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
      var match = !termo || texto.indexOf(termo) >= 0;
      tr.style.display = match ? '' : 'none';
      if (match) algumVisivel = true;
    });
    var header = div.querySelector('.nicho-header');
    var tabela = div.querySelector('.table-wrap');
    if (termo) {
      div.style.display = algumVisivel ? '' : 'none';
      if (tabela) tabela.style.display = 'block';
    } else {
      div.style.display = '';
      if (tabela) tabela.style.display = '';
    }
    if (algumVisivel) totalVisiveis += 1;
  });
  document.getElementById('contador').textContent = termo ? totalVisiveis + ' nichos encontrados' : '';
}

function mostrarToast(msg, cor) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = cor || '#333';
  t.style.display = 'block';
  setTimeout(function(){ t.style.display = 'none'; }, 4000);
}

function gerarRelatorio(nome, btn) {
  // Verifica se esta rodando localmente
  if (location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
    mostrarToast('Gere os relatorios localmente com: python serve_ranking.py', '#ff6f00');
    return;
  }
  var originalText = btn.textContent;
  btn.textContent = '...';
  btn.disabled = true;
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/gerar_relatorio?nome=' + encodeURIComponent(nome), true);
  xhr.onload = function() {
    try {
      var resp = JSON.parse(xhr.responseText);
      if (resp.status === 'existe' || resp.status === 'gerando') {
        btn.innerHTML = '<a class="btn-relatorio-existe" href="' + resp.pdf + '" target="_blank">PDF</a>';
        mostrarToast(resp.msg || 'Relatorio gerado!', '#34a853');
      } else {
        btn.textContent = originalText;
        btn.disabled = false;
        mostrarToast('Erro: ' + (resp.msg || 'Desconhecido'), '#d32f2f');
      }
    } catch(e) {
      btn.textContent = originalText;
      btn.disabled = false;
      mostrarToast('Erro ao conectar ao servidor', '#d32f2f');
    }
  };
  xhr.onerror = function() {
    btn.textContent = originalText;
    btn.disabled = false;
    mostrarToast('Erro de conexao. Execute python serve_ranking.py', '#d32f2f');
  };
  xhr.send();
}
</script>

<div id="toast"></div>
""")

nicho_order = sorted(nichos.keys(), key=lambda c: -len(nichos[c]))

for cat in nicho_order:
    empresas = nichos[cat]
    html.append(f'<div class="nicho">')
    html.append(f'<div class="nicho-header" onclick="toggleTabela(this)">')
    html.append(f'{cat} <span class="count">{len(empresas)} empresas</span></div>')
    html.append('<div class="table-wrap"><table><thead><tr><th>#</th><th>Empresa</th><th>Nota</th><th>Telefone</th><th>Redes</th><th>Google Maps</th><th>Relat\u00f3rio</th></tr></thead><tbody>')

    for i, c in enumerate(empresas, 1):
        nome = c.get('name', c.get('nome', '?'))
        rating = c.get('rating', 0) or 0
        reviews = c.get('reviews', 0) or 0
        phone = c.get('phone', '') or ''
        website = c.get('website', '') or ''
        map_link = c.get('map_link', '') or ''
        social = c.get('social', []) or []

        # Detecta oportunidade: rating alto (4.0+) mas sem site OU sem redes sociais
        has_website = bool(website)
        has_social = any(s.get('url') for s in social if isinstance(s, dict))
        is_oportunidade = rating >= 4.0 and (not has_website or not has_social)

        row_class = ' oportunidade' if is_oportunidade else ''
        html.append(f'<tr class="{row_class}">')
        html.append(f'<td>{i}</td>')

        # Nome
        html.append(f'<td><strong>{nome}</strong>')
        if is_oportunidade:
            html.append(f' <span class="badge-oportunidade">OPORTUNIDADE</span>')
        html.append('</td>')

        # Rating
        stars = '★' * int(round(rating)) + '☆' * (5 - int(round(rating)))
        html.append(f'<td><span class="rating">{stars}</span> <span class="reviews">({rating})</span><br><span class="reviews">{reviews} reviews</span></td>')

        # Phone / WhatsApp
        if phone:
            wa = phone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
            html.append(f'<td class="phone"><a href="https://wa.me/55{wa}" target="_blank">{phone}</a></td>')
        else:
            html.append('<td class="phone">-</td>')

        # Social links
        html.append('<td class="social">')
        social_urls = set()
        for s in social:
            if isinstance(s, dict):
                url = s.get('url', '')
            elif isinstance(s, str):
                url = s
            else:
                continue
            if url and url not in social_urls:
                social_urls.add(url)
                if 'instagram.com' in url:
                    html.append(f'<a class="ig" href="{url}" target="_blank">IG</a>')
                elif 'facebook.com' in url:
                    html.append(f'<a class="fb" href="{url}" target="_blank">FB</a>')
                elif 'youtube.com' in url or 'youtu.be' in url:
                    html.append(f'<a class="yt" href="{url}" target="_blank">YT</a>')
                elif 'tiktok.com' in url:
                    html.append(f'<a class="tt" href="{url}" target="_blank">TT</a>')
                elif 'linkedin.com' in url:
                    html.append(f'<a class="in" href="{url}" target="_blank">IN</a>')
                elif 'twitter.com' in url or 'x.com' in url:
                    html.append(f'<a class="tw" href="{url}" target="_blank">X</a>')
                else:
                    html.append(f'<a class="site" href="{url}" target="_blank">WEB</a>')
        if website and website not in social_urls:
            html.append(f'<a class="site" href="{website}" target="_blank">SITE</a>')
        if not social_urls and not website:
            html.append('<span style="color:#999">-</span>')
        html.append('</td>')

        # Google Maps link
        if map_link:
            html.append(f'<td class="map-link"><a href="{map_link}" target="_blank">Abrir Maps</a></td>')
        else:
            html.append('<td>-</td>')

        # Relatorio SEO button
        import re as _re
        safe_name = _re.sub(r'[\\/*?:"<>|]', '', nome[:50]).strip().replace(' ', '_')
        relatorio_path = os.path.join(os.path.dirname(__file__), 'relatorios', f"{safe_name}_relatorio.pdf")
        if os.path.exists(relatorio_path):
            html.append(f'<td class="relatorio"><a class="btn-relatorio-existe" href="relatorios/{safe_name}_relatorio.pdf" target="_blank">PDF</a></td>')
        else:
            html.append(f'<td class="relatorio"><button class="btn-relatorio" onclick="gerarRelatorio(\'{nome.replace(chr(39), chr(92)+chr(39))}\', this)">Gerar</button></td>')

        html.append('</tr>')

    html.append('</tbody></table></div></div>')

html.append("""
<div class="footer">
<p>Relat\u00f3rio gerado automaticamente pelo sistema de rastreamento Google Maps</p>
<p>Contato: Piter Mazini Mota - 73 98814-0990 - Pitemazini@gmail.com</p>
</div>
</body>
</html>
""")

with open(REPORT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(html))

print(f"Ranking gerado: {REPORT_FILE}")
print(f"Total de empresas: {len(companies)}")
print(f"Total de nichos: {len(nichos)}")

# Conta oportunidades
oportunidades = []
for c in companies:
    nome = c.get('name', c.get('nome', '?'))
    rating = c.get('rating', 0) or 0
    website = c.get('website', '') or ''
    social = c.get('social', []) or []
    has_website = bool(website)
    has_social = any(s.get('url') for s in social if isinstance(s, dict))
    if rating >= 4.0 and (not has_website or not has_social):
        oportunidades.append(c)

print(f"Oportunidades detectadas (rating 4.0+ sem site ou redes): {len(oportunidades)}")
for c in oportunidades[:20]:
    nome = c.get('name', c.get('nome', '?'))
    rating = c.get('rating', 0) or 0
    print(f"  - {nome} ({rating} estrelas)")
