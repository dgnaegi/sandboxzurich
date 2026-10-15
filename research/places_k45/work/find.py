import pickle,sys
o=pickle.load(open('osm_slim.pkl','rb'))
for q in sys.argv[1:]:
    print('##',q)
    n=0
    for t,i,la,lo,tg in o:
        s=' '.join(str(v) for k,v in tg.items() if k in('name','alt_name','old_name'))
        if q.lower() in s.lower():
            print(t,i,round(la,5),round(lo,5),tg.get('name'),tg.get('building') or tg.get('railway') or tg.get('amenity') or tg.get('leisure') or tg.get('highway') or '',tg.get('height',''));n+=1
            if n>6:break
