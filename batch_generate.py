import os, json, time, sys
sys.path.insert(0, os.path.dirname(__file__))

from generate_report import generate_report, save_report_as_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKED_FILE = os.path.join(BASE_DIR, "tracked_companies.json")
REPORT_LOG = os.path.join(BASE_DIR, "reports_generated.json")
BATCH_SIZE = 15

with open(TRACKED_FILE, encoding='utf-8') as f:
    companies = json.load(f)

if os.path.exists(REPORT_LOG):
    with open(REPORT_LOG, encoding='utf-8') as f:
        already = set(json.load(f))
else:
    already = set()

pendentes = [c for c in companies if c['name'] not in already]
total = len(pendentes)
print(f"{total} relatorios pendentes. Processando em lotes de {BATCH_SIZE}...")

batch_num = 0
while pendentes:
    batch = pendentes[:BATCH_SIZE]
    pendentes = pendentes[BATCH_SIZE:]
    batch_num += 1
    print(f"\n=== Lote {batch_num} ({len(batch)} relatorios, {len(pendentes)} restantes) ===")

    for i, company in enumerate(batch):
        nome = company['name']
        print(f"  [{i+1}/{len(batch)}] {nome[:60].encode('latin-1', errors='replace').decode('latin-1')}...", flush=True)

        report = generate_report(company)
        if not report:
            print(f"    Falha apos tentativas")
            continue

        filepath = save_report_as_pdf(company, report)
        print(f"    PDF salvo: {filepath}")
        already.add(nome)

        with open(REPORT_LOG, 'w', encoding='utf-8') as f:
            json.dump(sorted(already), f, indent=2, ensure_ascii=False)

        time.sleep(5)  # Rate limit entre chamadas

    # Pausa maior entre lotes
    if pendentes:
        print(f"  Aguardando 30s antes do proximo lote...")
        time.sleep(30)

print(f"\nConcluido! {len(already)} relatorios gerados.")
