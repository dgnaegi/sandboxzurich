import csv, sys
SKIP = ('school','kindergarten','childcare','social_facility','pitch','playground','artwork','information','university','library','place_of_worship','parking','bench','waste','toilets','recycling','bicycle_parking','fountain','post_box','atm','shelter','bus_station','hospital','doctors','clinic','dentist','pharmacy','community_centre','fire_station','police','townhall','courthouse','public_building','embassy','post_office','bank','swimming_pool','sports_centre','stadium','track','park','garden','grave_yard','construction','vacant')
rows = list(csv.DictReader(open('todo.csv', encoding='utf-8')))
keep = [r for r in rows if not any(s in (r['kind'] or '') for s in SKIP)]
print('keep', len(keep), 'of', len(rows))
n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for r in keep[start:start+n]:
    print('|'.join([r['osm_id'], r['name'], r['kind'], r['address'], r['website']]))
