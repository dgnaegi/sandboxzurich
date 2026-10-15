import json,urllib.request,urllib.parse,time
UA='gtazurich-research/1.0 (daniel.gnaegi@outlook.com)'
def g(**p):
    p['format']='json';return json.load(urllib.request.urlopen(urllib.request.Request('https://de.wikipedia.org/w/api.php?'+urllib.parse.urlencode(p),headers={'User-Agent':UA}),timeout=30))
for q in ['Bahnhof Zürich Altstetten','Bahnhof Zürich Wiedikon','Hohlstrasse Zürich','Badenerstrasse Zürich','Lindenplatz Altstetten','Schmiede Wiedikon Zürich','Alte Kirche Altstetten','Westlink Zürich']:
    s=g(action='query',list='search',srsearch=q,srlimit=2)['query']['search']
    print(q,'->',[x['title'] for x in s])
    if not s:continue
    t=s[0]['title']
    e=list(g(action='query',prop='extracts',explaintext=1,exsectionformat='plain',titles=t)['query']['pages'].values())[0].get('extract','')
    open('wp_'+q.replace(' ','_')+'.txt','w').write(t+'\n'+e);time.sleep(1)
