import os, json, time, sys
from datetime import datetime

# Reuse the existing search function
sys.path.insert(0, os.path.dirname(__file__))
from google_maps_tracker import search_google_maps, load_tracked_companies, save_tracked_companies

REGIONS = [
    "Entroncamento de Jaguaquara, Bahia",
    "Jaguaquara, Bahia",
    "Itiruçu, Bahia",
]

TERMOS = []
for r in REGIONS:
    TERMOS += [
        f"advocacia advogado escritorio em {r}",
        f"acougue carne frigorifico em {r}",
        f"borracharia pneu recapagem em {r}",
        f"lava jato lavagem carro em {r}",
        f"auto escola formacao condutores em {r}",
        f"clinica medica medico especialista em {r}",
        f"funilaria pintura automotiva em {r}",
        f"mecanico eletricista encanador pintor pedreiro em {r}",
        f"oficinas auto pecas borracharias em {r}",
        f"refrigeracao ar condicionado geladeira em {r}",
    ]

tracked = load_tracked_companies()
existing = {(c.get('name',''), c.get('address','')) for c in tracked}

novas = 0
for termo in TERMOS:
    print(f"Buscando: {termo}...", flush=True)
    batch = search_google_maps(termo)
    for item in batch:
        key = (item['name'], item.get('address',''))
        if key not in existing:
            item['first_seen'] = datetime.now().isoformat()
            tracked.append(item)
            existing.add(key)
            novas += 1
            nome = item['name'].encode('latin-1', errors='replace').decode('latin-1')
            print(f"  NOVA: {nome}")
        else:
            for t in tracked:
                if (t.get('name',''), t.get('address','')) == key:
                    t['rating'] = item.get('rating', t.get('rating', 0))
                    t['reviews'] = item.get('reviews', t.get('reviews', 0))
                    t['phone'] = item.get('phone', t.get('phone', ''))
                    t['website'] = item.get('website', t.get('website', ''))
                    t['map_link'] = item.get('map_link', t.get('map_link', ''))
                    break
    print(f"  +{len(batch)} encontradas ({novas} novas ate agora)", flush=True)
    time.sleep(2)
    # Salva a cada termo
    save_tracked_companies(tracked)

print(f"Total novas: {novas}")
print(f"Total geral: {len(tracked)}")
