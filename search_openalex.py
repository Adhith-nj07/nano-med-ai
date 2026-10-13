import urllib.request
import urllib.parse
import json

query = '"machine learning" AND "drug release" AND "PLGA" AND dataset'
params = urllib.parse.urlencode({'search': query, 'per-page': 5})
url = f'https://api.openalex.org/works?{params}'

req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())
    for result in data.get('results', []):
        print(f"Title: {result.get('title')}")
        print(f"DOI: {result.get('doi')}")
        print('---')
