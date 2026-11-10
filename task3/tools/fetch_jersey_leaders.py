"""Refresh the checked-in leader snapshots; normal Power BI refresh remains offline."""
import requests, bs4, re, json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fetch(n):
    ordinal='1re' if n==1 else f'{n}e'
    url=f'https://fr.wikipedia.org/wiki/{ordinal}_%C3%A9tape_du_Tour_de_France_2025'
    r=requests.get(url,timeout=30,headers={'User-Agent':'TourDeFranceCoursework/1.0 (educational classification data verification)'})
    r.raise_for_status()
    soup=bs4.BeautifulSoup(r.text,'html.parser')
    output=[]
    for cat,title in [('Points','Classement par points'),('Mountains','Classement du meilleur grimpeur')]:
        table=next(t for t in soup.find_all('table') if not t.find('table') and t.get_text(' ',strip=True).startswith(title))
        row=next(tr for tr in table.find_all('tr') if len(tr.find_all('td',recursive=False))==5 and tr.find('td').get_text(' ',strip=True)=='1 er')
        cells=[td.get_text(' ',strip=True) for td in row.find_all('td',recursive=False)]
        assert cells[0]=='1 er',cells
        output.append({'Stage':n,'Classification':cat,'Leader':cells[1],'Points':int(re.search(r'\d+',cells[4])[0]),'Source':r.url})
    return output
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=[r for group in pool.map(fetch,range(1,22)) for r in group]
    (ROOT/'data/jersey_leaders.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for r in rows:print(r['Stage'],r['Classification'],r['Leader'],r['Points'])

