import urllib.request
import re

url = 'https://www.nature.com/articles/s41598-024-82728-6'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        links = re.findall(r'href=[\'\"]?([^\'\" >]+)[\'\"]?', html, re.I)
        supp_links = [l for l in links if 'supp' in l.lower() or '41598_' in l.lower()]
        print('Supplementary links found:')
        for l in set(supp_links):
            print(l)
except Exception as e:
    print('Error:', e)
