import json,time,sys,re,os,urllib.request,urllib.parse
UA='gtazurich-research/1.0 (daniel.gnaegi@outlook.com)'
OUT='/Users/danielgnagi/gtazurich/data/raw/photos/places'
PL={
'altstetten_bahnhof':{'geo':[(47.3913,8.4885,350),(47.3922,8.4880,250)],'q':['Bahnhof Zürich Altstetten','Passerelle Altstetten Bahnhof']},
'lindenplatz':{'geo':[(47.3878,8.4848,250)],'q':['Lindenplatz Zürich Altstetten','Reformierte Kirche Altstetten Zürich','Altstetten Dorfkern']},
'hohlstrasse_k9':{'geo':[(47.3896,8.4946,300),(47.3881,8.5016,300),(47.3912,8.4792,250),(47.3873,8.4990,250)],'q':['Hohlstrasse Zürich Altstetten','Hohlstrasse Zürich']},
'wiedikon_bahnhof':{'geo':[(47.3716,8.5230,300)],'q':['Bahnhof Zürich Wiedikon','Zürich Wiedikon Bahnhof Brücke']},
'schmiede_wiedikon':{'geo':[(47.3701,8.5245,250)],'q':['Schmiede Wiedikon','Birmensdorferstrasse Zürich Wiedikon']},
'badenerstrasse':{'geo':[(47.3830,8.4930,300),(47.3800,8.4960,250),(47.3850,8.4890,250),(47.3782,8.4985,200)],'q':['Badenerstrasse Zürich Altstetten','Badenerstrasse Albisrieden Zürich','Albisriederplatz Zürich']},
}
def api(**p):
    p['format']='json';u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(p)
    for i in range(6):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=40);time.sleep(1.2);return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(20*(i+1)); continue
            raise
cand={}
for k,v in PL.items():
    c={}
    for la,lo,r in v['geo']:
        for t in api(action='query',list='geosearch',gscoord=f'{la}|{lo}',gsradius=r,gslimit=60,gsnamespace=6).get('query',{}).get('geosearch',[]):
            c[t['title']]=t.get('dist',999)
    for q in v['q']:
        for t in api(action='query',list='search',srsearch=q,srnamespace=6,srlimit=25).get('query',{}).get('search',[]):
            c.setdefault(t['title'],500)
    cand[k]=c;print(k,len(c),flush=True)
json.dump(cand,open('cand.json','w'),ensure_ascii=False)
