import urllib.request
import re

url = 'https://www.nature.com/articles/s41467-022-35343-w'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        links = re.findall(r'href=[\'\"]?([^\'\" >]+)[\'\"]?', html, re.I)
        supp_links = [l for l in links if 'supp' in l.lower() or '41467_2022_35343' in l.lower()]
        print('Supplementary links found:')
        for l in set(supp_links):
            print(l)
except Exception as e:
    print('Error:', e)
