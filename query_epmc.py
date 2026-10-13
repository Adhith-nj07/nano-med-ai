import urllib.request
import json
import os

url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(nanoparticle+OR+liposome)+AND+(stability+OR+aggregation)+AND+(DLS+OR+hydrodynamic)+AND+(time+OR+days+OR+months)&format=json&resultType=core&pageSize=30'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        hits = data.get('resultList', {}).get('result', [])
        print(f'Found {len(hits)} papers in the pilot search.')
        
        has_supp = 0
        for hit in hits:
            supp = hit.get('hasSuppl', 'N')
            if supp == 'Y':
                has_supp += 1
                
        print(f'Papers with supplementary data: {has_supp}')
        for hit in hits[:5]:
            print(f"- {hit.get('id')}: {hit.get('title')} (Supp: {hit.get('hasSuppl', 'N')})")
except Exception as e:
    print('Error:', e)
