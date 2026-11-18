"""Rebuild the local atlas and computed Topographical practice bank.

Input: research/maps/greater-london-latest.osm.pbf (Geofabrik/ODbL).
No remote map tiles are requested. This is deliberately a small, reproducible
Pillow renderer rather than a server or a hidden runtime map dependency.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import gzip
import heapq
import json
import math
import random
import re
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'research/maps'
APP = ROOT / 'app'
BBOX = (51.475, -0.225, 51.565, -0.045)  # south, west, north, east
SEED = 20261118
SOURCE = 'https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html'
DATE = '2026-11-18'
DRIVE = {'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','living_street','service'}
DENY = {'no','private','customers','delivery','agricultural','forestry','permit','destination'}
CATEGORIES = {'hospital':'Hospital','police':'Police facility','fire_station':'Fire station','place_of_worship':'Place of worship','station':'Railway station','parking':'Car park','fuel':'Petrol station','school':'School','museum':'Museum','theatre':'Theatre','hotel':'Hotel'}
SYMBOLS = {'hospital':'H','police':'P','fire_station':'F','place_of_worship':'+','station':'S','parking':'P','fuel':'F','school':'Sc','museum':'M','theatre':'T','hotel':'Ho'}
COLORS = {'hospital':'#b62032','police':'#243f88','fire_station':'#b65c22','place_of_worship':'#674374','station':'#563b36','parking':'#2272a5','fuel':'#766235','school':'#4c496d','museum':'#765888','theatre':'#765888','hotel':'#78654c'}

def dump_js(path, name, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending=path.with_suffix(path.suffix+'.tmp');pending.write_text('/* Generated from OpenStreetMap; database ODbL-1.0. */\nwindow.' + name + ' = ' + json.dumps(value, ensure_ascii=False, separators=(',',':')) + ';\n', encoding='utf-8');pending.replace(path)

def cache_read(name):
    zipped=WORK/(name+'.gz')
    if zipped.exists():
        with gzip.open(zipped,'rt',encoding='utf-8') as stream:return json.load(stream)
    return json.loads((WORK/name).read_text(encoding='utf-8'))

def cache_write(name,value):
    with gzip.open(WORK/(name+'.gz'),'wt',encoding='utf-8',compresslevel=6) as stream:json.dump(value,stream,separators=(',',':'))

def distance(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,(a[0],a[1],b[0],b[1]))
    return 6371008.8*2*math.asin(min(1,math.sqrt(math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2)))

def inside(lat,lon,pad=0):
    s,w,n,e=BBOX
    return s-pad <= lat <= n+pad and w-pad <= lon <= e+pad

def category(t):
    for k in ('amenity','tourism','railway'):
        if t.get(k) in CATEGORIES:
            return t[k]
    return None

def drivable(t):
    if t.get('highway') not in DRIVE: return False
    # Specific motorcar permissions override general access, as in OSM.
    access=next((t[k] for k in ('motorcar','motor_vehicle','vehicle','access') if k in t), 'yes')
    if access in DENY: return False
    if t.get('service') in {'parking_aisle','driveway','emergency_access'}: return False
    if t.get('busway') or t.get('highway')=='busway': return False
    # Time-dependent rules cannot be represented truthfully by a fixed exam map.
    if any(k in t for k in ('motor_vehicle:conditional','motorcar:conditional','access:conditional','vehicle:conditional')): return False
    return True

def extract():
    import osmium
    class Handler(osmium.SimpleHandler):
        def __init__(self):
            super().__init__(); self.roads=[]; self.areas=[]; self.pois=[]; self.relations=[]; self.barriers=[]
        def node(self,n):
            if not n.location.valid(): return
            lat,lon=n.location.lat,n.location.lon
            if not inside(lat,lon): return
            t=dict(n.tags); cat=category(t)
            if cat and t.get('name'):
                self.pois.append({'id':'n'+str(n.id),'name':t['name'],'category':cat,'lat':lat,'lng':lon,'osmType':'node','osmId':str(n.id)})
            if t.get('barrier') in {'bollard','block','bus_trap','cycle_barrier'} and t.get('motor_vehicle')!='yes':
                self.barriers.append(str(n.id))
        def way(self,w):
            t=dict(w.tags)
            wanted=t.get('highway') or t.get('building') or t.get('landuse') or t.get('leisure') or t.get('natural')=='water' or t.get('waterway') or category(t)
            if not wanted: return
            if not all(n.location.valid() for n in w.nodes): return
            pts=[[round(n.lat,7),round(n.lon,7)] for n in w.nodes]
            if not pts or not any(inside(*p) for p in pts): return
            if t.get('highway'):
                self.roads.append({'id':str(w.id),'nodes':[str(n.ref) for n in w.nodes],'geometry':pts,'name':t.get('name',''),'ref':t.get('ref',''),'highway':t['highway'],'tags':{k:v for k,v in t.items() if k in ('oneway','access','motorcar','motor_vehicle','vehicle','busway','service','junction','layer','bridge','tunnel','motor_vehicle:conditional','motorcar:conditional','access:conditional','vehicle:conditional')},'drivable':drivable(t)})
            typ=None
            if t.get('natural')=='water' or t.get('waterway') in {'riverbank','dock'}: typ='water'
            elif t.get('waterway') in {'river','canal','stream'}: typ='waterline'
            elif t.get('leisure') in {'park','garden','recreation_ground','golf_course','pitch'} or t.get('landuse') in {'grass','recreation_ground','forest','cemetery','village_green'}: typ='park'
            elif t.get('building'): typ='building'
            if typ:
                self.areas.append({'id':str(w.id),'type':typ,'geometry':pts,'name':t.get('name','')})
            cat=category(t)
            if cat and t.get('name'):
                lat=sum(p[0] for p in pts)/len(pts); lon=sum(p[1] for p in pts)/len(pts)
                if inside(lat,lon): self.pois.append({'id':'w'+str(w.id),'name':t['name'],'category':cat,'lat':round(lat,7),'lng':round(lon,7),'osmType':'way','osmId':str(w.id)})
        def relation(self,r):
            t=dict(r.tags)
            if t.get('type')=='restriction':
                self.relations.append({'id':str(r.id),'restriction':t.get('restriction:motorcar',t.get('restriction:motor_vehicle',t.get('restriction',''))),'conditional':any('conditional' in k for k in t),'except':t.get('except',''),'members':[{'type':m.type,'ref':str(m.ref),'role':m.role} for m in r.members]})
    h=Handler(); h.apply_file(str(WORK/'greater-london-latest.osm.pbf'), locations=True, idx='flex_mem')
    unique={}
    for p in h.pois:
        # A node and its containing building often name the same POI.
        key=(p['name'].casefold(),p['category'])
        if key not in unique: unique[key]=p
    data={'roads':h.roads,'areas':h.areas,'pois':list(unique.values()),'relations':h.relations,'barriers':h.barriers}
    cache_write('extracted.json',data)
    print('Extracted', {k:len(v) for k,v in data.items()},flush=True)
    return data

def extract_areas(data):
    """OSM water/parks frequently live on relations rather than tagged ways."""
    import osmium
    class Areas(osmium.SimpleHandler):
        def __init__(self):super().__init__();self.items=[]
        def area(self,a):
            t=dict(a.tags);typ=None
            if t.get('natural')=='water' or t.get('waterway') in {'riverbank','dock'}:typ='water'
            elif t.get('leisure') in {'park','garden','recreation_ground'}:typ='park'
            if not typ:return
            for ring in a.outer_rings():
                pts=[[round(n.lat,7),round(n.lon,7)] for n in ring if n.location.valid()]
                if len(pts)>2 and any(inside(*p) for p in pts):
                    self.items.append({'id':'area'+str(a.id),'type':typ,'geometry':pts,'name':t.get('name','')})
    h=Areas();h.apply_file(str(WORK/'greater-london-latest.osm.pbf'),locations=True,idx='flex_mem')
    data['areas'].extend(h.items);data['areaRelationsExtracted']=True
    cache_write('extracted.json',data)
    print('Area multipolygons',len(h.items),flush=True)
    return data

def graph(data):
    import networkx as nx
    roads=[r for r in data['roads'] if r['drivable']]
    uses=collections.Counter(n for r in roads for n in set(r['nodes']))
    barriers=set(data['barriers']); nodes={}; edges=[]
    # Preserve actual OSM junctions, way ends and shape vertices at least 75 m apart.
    for r in roads:
        ns=r['nodes']; ps=r['geometry']; start=0; accumulated=0
        for i in range(1,len(ns)):
            accumulated += distance(ps[i-1],ps[i])
            split=uses[ns[i]]>1 or i==len(ns)-1 or ns[i] in barriers or accumulated>=75
            if not split: continue
            a,b=ns[start],ns[i]; shape=ps[start:i+1]; start=i; accumulated=0
            if a==b or a in barriers or b in barriers: continue
            if not all(inside(*p) for p in shape): continue
            length=round(sum(distance(x,y) for x,y in zip(shape,shape[1:])),2)
            if length<0.1: continue
            for nid,p in ((a,shape[0]),(b,shape[-1])): nodes[nid]={'id':nid,'lat':p[0],'lng':p[1]}
            one=r['tags'].get('oneway','yes' if r['tags'].get('junction')=='roundabout' else 'no')
            directions=[1] if one in {'yes','1','true'} else [-1] if one=='-1' else [1,-1]
            for direction in directions:
                eid='e'+str(len(edges))
                edges.append({'id':eid,'from':a if direction==1 else b,'to':b if direction==1 else a,'length':length,'name':r['name'],'ref':r['ref'],'oneway':len(directions)==1,'geometry':shape if direction==1 else list(reversed(shape)),'osmWay':r['id'],'highway':r['highway'],'access':'yes'})
    # Keep largest strongly connected component: no artificial ferries/connectors.
    g=nx.DiGraph(); g.add_edges_from((e['from'],e['to']) for e in edges)
    keep=max(nx.strongly_connected_components(g),key=len)
    edges=[e for e in edges if e['from'] in keep and e['to'] in keep]
    nodes={k:v for k,v in nodes.items() if k in keep}
    byway=collections.defaultdict(list); outgoing=collections.defaultdict(list)
    for e in edges: byway[e['osmWay']].append(e); outgoing[e['from']].append(e)
    restrictions=[]; unsupported=[]
    for r in data['relations']:
        m=r['members']; fr=[x['ref'] for x in m if x['role']=='from' and x['type']=='w']; to=[x['ref'] for x in m if x['role']=='to' and x['type']=='w']; via=[x['ref'] for x in m if x['role']=='via' and x['type']=='n']
        if not any(x in byway for x in fr): continue
        if r['conditional'] or len(via)!=1 or not fr or not to:
            unsupported.append(r['id']); continue
        if any(x in {'motorcar','motor_vehicle','vehicle'} for x in r['except'].split(';')): continue
        v=via[0]
        for a in [e for x in fr for e in byway[x] if e['to']==v]:
            candidates=[e for e in outgoing[v] if (e['osmWay'] not in to if r['restriction'].startswith('only_') else e['osmWay'] in to)]
            for b in candidates:
                if r['restriction']=='no_u_turn' and b['to']!=a['from']: continue
                restrictions.append({'fromEdge':a['id'],'viaNode':v,'toEdge':b['id'],'type':'no_turn','osmRelation':r['id'],'label':r['restriction']})
    # POIs snapped to an actual drivable vertex within 100 m. The marker defines
    # the exam set-down point; no invented entrance/driveway is implied.
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    nlist=list(nodes.values()); tree=STRtree([Point(n['lng']*math.cos(math.radians(51.52)),n['lat']) for n in nlist])
    pois=[]
    for p in data['pois']:
        idx=int(tree.nearest(Point(p['lng']*math.cos(math.radians(51.52)),p['lat'])))
        n=nlist[idx]; dist=distance((p['lat'],p['lng']),(n['lat'],n['lng']))
        if dist<=100:
            p=dict(p,node=n['id'],snapDistance=round(dist,1)); pois.append(p)
    result={'bounds':[[BBOX[0],BBOX[1]],[BBOX[2],BBOX[3]]],'minZoom':12,'maxZoom':17,'tileSize':256,'nodes':list(nodes.values()),'edges':edges,'restrictions':restrictions,'pois':pois,'source':SOURCE,'accessed':DATE,'licence':'ODbL-1.0','unsupportedRestrictions':unsupported,'coverage':'Central London practice area; map markers define the exercise set-down points.'}
    print('Graph',len(nodes),'nodes',len(edges),'directed edges',len(restrictions),'turn restrictions',len(pois),'POIs',len(unsupported),'unsupported conditional/via-way restrictions',flush=True)
    return result

class Router:
    def __init__(self,g):
        self.g=g; self.nodes={n['id']:n for n in g['nodes']}; self.edges={e['id']:e for e in g['edges']}; self.out=collections.defaultdict(list)
        for e in g['edges']: self.out[e['from']].append(e)
        self.banned={(r['fromEdge'],r['toEdge']) for r in g['restrictions']}
    def path(self,start,end,closed=(),penalty=None):
        closed=set(closed); todo=[(0,start,'')]; cost={(start,''):0}; prev={}; final=None
        while todo:
            d,n,last=heapq.heappop(todo)
            if d!=cost.get((n,last)): continue
            if n==end: final=(n,last); break
            for e in self.out[n]:
                if e['id'] in closed or (last,e['id']) in self.banned: continue
                key=(e['to'],e['id']); nd=d+e['length']+(penalty.get(e['id'],0) if penalty else 0)
                if nd<cost.get(key,float('inf')):
                    cost[key]=nd; prev[key]=(n,last); heapq.heappush(todo,(nd,*key))
        if final is None: return None
        route=[]
        while final in prev:
            route.append(final[1]); final=prev[final]
        route.reverse()
        return route
    def length(self,path): return round(sum(self.edges[e]['length'] for e in path),2)
    def node_path(self,path): return [self.edges[path[0]]['from']]+[self.edges[e]['to'] for e in path]
    def coords(self,path):
        return [p for i,e in enumerate(path) for p in self.edges[e]['geometry'][0 if i==0 else 1:]]

def turn_instructions(path,router):
    def bearing(a,b):
        return math.degrees(math.atan2((b[1]-a[1])*math.cos(math.radians((a[0]+b[0])/2)),b[0]-a[0]))
    result=[];prior=None
    for eid in path:
        edge=router.edges[eid];name=edge['name'] or 'unnamed connecting road'
        if prior is None:result.append('Leave by '+name)
        elif name!=(prior['name'] or 'unnamed connecting road'):
            incoming=bearing(prior['geometry'][-2],prior['geometry'][-1]);outgoing=bearing(edge['geometry'][0],edge['geometry'][1]);delta=(outgoing-incoming+180)%360-180
            action='Turn right into ' if delta>30 else 'Turn left into ' if delta<-30 else 'Continue into '
            if abs(delta)>150:action='Turn back into '
            result.append(action+name)
        prior=edge
    if prior:result.append('Set down on '+(prior['name'] or 'unnamed connecting road'))
    return result

def make_routes(g):
    router=Router(g); rng=random.Random(SEED); pois=list(g['pois']); rng.shuffle(pois)
    choices=[p for p in pois if p['category'] in {'hospital','museum','theatre','station','hotel','place_of_worship'}]
    routes=[]; used=set(); counts=collections.Counter(); targets={'short':60,'closure':40,'long':40}
    for attempt in range(15000):
        if all(counts[k]>=v for k,v in targets.items()): break
        a,b=rng.sample(choices,2)
        if (a['node'],b['node']) in used or a['name']==b['name']: continue
        air=distance((a['lat'],a['lng']),(b['lat'],b['lng']))
        kind='long' if counts['long']<40 and 4000<air<9000 else 'short' if counts['short']<60 and 800<air<2200 else 'closure' if counts['closure']<40 and 700<air<2000 else None
        if not kind: continue
        path=router.path(a['node'],b['node'])
        if not path: continue
        before=path; closed=[]; street=''
        if kind=='closure':
            names=[router.edges[e]['name'] for e in path[1:-1] if router.edges[e]['name'] and router.edges[e]['highway'] not in {'motorway','trunk','motorway_link'}]
            if not names: continue
            rng.shuffle(names)
            for name in names[:6]:
                closure=[e['id'] for e in g['edges'] if e['name']==name]
                candidate=router.path(a['node'],b['node'],closure)
                if candidate and 1000<=router.length(candidate)<=3000 and router.length(candidate)>router.length(before)+20:
                    path=candidate;closed=closure;street=name;break
            if not closed: continue
        length=router.length(path)
        low,high=(5000,12000) if kind=='long' else (1000,3000)
        if not low<=length<=high: continue
        points=router.coords(path); padLat=0.003; padLng=0.0048
        bounds=[[max(BBOX[0],min(p[0] for p in points)-padLat),max(BBOX[1],min(p[1] for p in points)-padLng)],[min(BBOX[2],max(p[0] for p in points)+padLat),min(BBOX[3],max(p[1] for p in points)+padLng)]]
        streets=[]
        for e in path:
            name=router.edges[e]['name'] or 'unnamed connecting road'
            if not streets or streets[-1]!=name: streets.append(name)
        # Up to three alternatives, selected by small edge penalties and then
        # measured by real distance. Never call a penalised route 'optimal'.
        acceptable=[]
        for fraction in (.03,.1,.3):
            alt=router.path(a['node'],b['node'],closed,{e:router.edges[e]['length']*fraction for e in path})
            if alt and alt!=path and router.length(alt)<=1.05*length and not any(x['edges']==alt for x in acceptable):
                acceptable.append({'nodes':router.node_path(alt),'edges':alt,'length':router.length(alt)})
        rid='TOPO-'+kind.upper()+'-'+str(counts[kind]+1).zfill(3)
        item={'id':rid,'type':'route','routeType':kind,'section':'Route planning','question':f'What is the most direct route between {a["name"]} (the green marker) and {b["name"]} (the red marker)?'+(f' NOTE: {street} is CLOSED.' if closed else ''),'start':a['node'],'end':b['node'],'startName':a['name'],'endName':b['name'],'startPOI':a['id'],'endPOI':b['id'],'optimal':router.node_path(path),'optimalEdges':path,'optimalGeometry':points,'optimalLength':length,'closedEdges':closed,'closedStreet':street,'unclosedOptimalEdges':before,'bounds':bounds,'acceptable':acceptable,'streets':streets,'marks':22,'difficulty':3 if kind=='long' else 2,'explanation':f'The shortest legal route in this exercise is {length/1000:.2f} km. Follow the green dashed route and the ordered street list.','source':SOURCE,'evidence':{'startOSM':a['osmType']+'/'+a['osmId'],'endOSM':b['osmType']+'/'+b['osmId'],'method':'distance-weighted Dijkstra with incoming-edge state; visible turn restrictions and closure applied'}}
        routes.append(item); used.add((a['node'],b['node'])); counts[kind]+=1
        if len(routes)%20==0: print('Routes',dict(counts),flush=True)
    if dict(counts)!=targets: raise RuntimeError(('Insufficient routes',dict(counts)))
    return routes

def mercator(lat,lon,z):
    size=256*2**z
    return ((lon+180)/360*size,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*size)

def unmercator(x,y,z):
    size=256*2**z
    return (math.degrees(math.atan(math.sinh(math.pi*(1-2*y/size)))),x/size*360-180)

@lru_cache(maxsize=64)
def font(size,bold=False):
    from PIL import ImageFont
    paths=[APP/'vendor/fonts/NotoSans-Bold.ttf' if bold else APP/'vendor/fonts/NotoSans-Regular.ttf',Path('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf')]
    for p in paths:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

@lru_cache(maxsize=20000)
def font_bbox(text,size,bold=False):
    return font(size,bold).getbbox(text)

class Atlas:
    def __init__(self,data,g):
        from shapely.geometry import box
        from shapely.strtree import STRtree
        self.data=data; self.g=g; self.projected={}; self.box=box; self.STRtree=STRtree;self.enabled=True
    def at_zoom(self,z):
        if z in self.projected: return self.projected[z]
        if len(self.projected)>=3:self.projected.pop(next(iter(self.projected)))
        result={}
        for kind,items in [('roads',self.data['roads']),('areas',self.data['areas'])]:
            feats=[]; boxes=[]
            for item in items:
                pts=[mercator(*p,z) for p in item['geometry']]
                bbox=(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))
                feats.append((item,pts,bbox)); boxes.append(self.box(*bbox))
            result[kind]=(feats,self.STRtree(boxes))
        self.projected[z]=result
        return result
    def render(self,z,origin,width,height,labels=True,focus=None):
        from PIL import Image,ImageDraw
        img=Image.new('RGB',(width,height),'#f4e7e4'); draw=ImageDraw.Draw(img)
        ox,oy=origin; query=self.box(ox-150,oy-150,ox+width+150,oy+height+150); data=self.at_zoom(z)
        area_feats,area_tree=data['areas']; road_feats,road_tree=data['roads']
        areas=[area_feats[int(i)] for i in area_tree.query(query)]; roads=[road_feats[int(i)] for i in road_tree.query(query)]
        def shift(points): return [(round(x-ox,2),round(y-oy,2)) for x,y in points]
        for item,pts,bb in sorted(areas,key=lambda a:{'building':0,'park':1,'water':2,'waterline':3}[a[0]['type']]):
            typ=item['type']; p=shift(pts)
            if len(p)<2: continue
            if typ=='waterline': draw.line(p,fill='#acd6df',width=max(2,round(3*2**(z-14))))
            elif len(p)>2:
                if typ=='building' and z<16: continue
                fill={'building':'#e6c6c8','park':'#c6dcae','water':'#acd6df'}[typ]
                draw.polygon(p,fill=fill,outline='#dab1b5' if typ=='building' and z>=17 else None)
        roads.sort(key=lambda x: {'motorway':6,'trunk':5,'primary':4,'secondary':3,'tertiary':2}.get(x[0]['highway'],1))
        for casing in (True,False):
            for r,pts,bb in roads:
                typ=r['highway']; major=typ in {'motorway','trunk','primary','secondary','tertiary','primary_link','secondary_link','trunk_link'}
                if z<=13 and not major: continue
                if typ in {'footway','path','steps','cycleway','bridleway'}:
                    if casing or z<16: continue
                    draw.line(shift(pts),fill='#b4a4a2',width=1); continue
                base=10 if major else 6
                linew=max(1,round(base*2**((z-16)*.55)))
                if casing: linew+=2
                fill='#68625b' if casing else '#f4cc69' if major else '#fffaf4' if r['drivable'] else '#eabac5'
                draw.line(shift(pts),fill=fill,width=linew,joint='curve')
        occupied=[]; visible_names=set()
        def clear(b): return not any(not(b[2]<a[0] or b[0]>a[2] or b[3]<a[1] or b[1]>a[3]) for a in occupied)
        def label(text,x,y,size,color='#302f2e',bg=None,force=False,bold=False):
            f=font(size,bold); b=font_bbox(text,size,bold); tw,th=b[2]-b[0],b[3]-b[1]; rect=(x-tw/2-3,y-th/2-3,x+tw/2+3,y+th/2+3)
            if not force and (rect[0]<2 or rect[1]<2 or rect[2]>width-2 or rect[3]>height-2 or not clear(rect)): return False
            if bg: draw.rounded_rectangle(rect,2,fill=bg)
            draw.text((x-tw/2,y-th/2-b[1]),text,font=f,fill=color,stroke_width=1 if bg is None else 0,stroke_fill='#fffaf5')
            occupied.append(rect); return True
        if labels:
            # Deterministic global label centres keep labels coherent across metatiles.
            seen=set()
            for r,pts,bb in sorted(roads,key=lambda x:(0 if x[0]['ref'] else 1,-sum(math.dist(a,b) for a,b in zip(x[1],x[1][1:])))):
                name=r['name']; major=bool(r['ref'])
                if not name or (z<15 and not major) or (name in seen and not focus): continue
                lengths=[math.dist(a,b) for a,b in zip(pts,pts[1:])]; total=sum(lengths)
                if total<35 and not focus: continue
                mid=pts[len(pts)//2] if len(pts)>2 else ((pts[0][0]+pts[-1][0])/2,(pts[0][1]+pts[-1][1])/2)
                x,y=mid[0]-ox,mid[1]-oy
                text=name.upper()+((' '+r['ref']) if r['ref'] else '')
                if label(text,x,y,max(10,min(14,z-3)),bg='#fff8dd' if major else None): seen.add(name);visible_names.add(name)
            for item,pts,bb in areas:
                if item['type'] not in {'park','water'} or not item['name']: continue
                x=(bb[0]+bb[2])/2-ox;y=(bb[1]+bb[3])/2-oy
                name=' '.join(item['name'].upper()) if item['type']=='water' else item['name'].upper()
                label(name,x,y,12,color='#456840' if item['type']=='park' else '#316b7e')
            if z>=16 or focus:
                for p in self.g['pois']:
                    x,y=mercator(p['lat'],p['lng'],z);x-=ox;y-=oy
                    if 12<x<width-12 and 12<y<height-12:
                        self.symbol(draw,p['category'],x,y)
                        if z>=17: label(p['name'],x+25,y-16,11,color=COLORS[p['category']])
            if z>=15:
                for r,pts,bb in roads:
                    if not r['drivable'] or r['tags'].get('oneway') not in {'yes','1','true','-1'}: continue
                    if len(pts)<2: continue
                    k=len(pts)//2; a,b=pts[max(0,k-1)],pts[k]; a,b=shift([a,b])
                    if r['tags']['oneway']=='-1':a,b=b,a
                    self.arrow(draw,a,b,'#3a4348',10)
        # Every represented turn restriction is drawn; UI can also overlay the
        # precise from/via/to movement for accessibility at small zoom levels.
        if z>=15:
            ns={n['id']:n for n in self.g['nodes']}; shown=set()
            for r in self.g['restrictions']:
                if r['viaNode'] in shown: continue
                shown.add(r['viaNode']); n=ns[r['viaNode']]; x,y=mercator(n['lat'],n['lng'],z);x-=ox;y-=oy
                if 0<x<width and 0<y<height:
                    draw.ellipse((x-6,y-6,x+6,y+6),fill='#fffaf4',outline='#bc2f3f',width=2);draw.line((x-4,y+4,x+4,y-4),fill='#bc2f3f',width=2)
        return img,visible_names
    @staticmethod
    def arrow(draw,a,b,color,size):
        dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
        if length<2:return
        ux,uy=dx/length,dy/length; x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
        tip=(x+ux*size/2,y+uy*size/2); tail=(x-ux*size/2,y-uy*size/2)
        head=5 if size<20 else min(13,size*.5);side=head*.65
        draw.line((tail,tip),fill=color,width=2 if size<20 else 4)
        draw.polygon([tip,(tip[0]-ux*head-uy*side,tip[1]-uy*head+ux*side),(tip[0]-ux*head+uy*side,tip[1]-uy*head-ux*side)],fill=color,outline='#ffffff' if size>=20 else None,width=1)
    @staticmethod
    def symbol(draw,cat,x,y,size=10):
        draw.rounded_rectangle((x-size,y-size,x+size,y+size),3,fill='#fffdf8',outline=COLORS[cat],width=2)
        f=font(12,True); text=SYMBOLS[cat]; b=font_bbox(text,12,True)
        draw.text((x-(b[2]-b[0])/2,y-(b[3]-b[1])/2-b[1]),text,font=f,fill=COLORS[cat])
    def static(self,centre,z=16,offset=(0,0),focus=None):
        from PIL import Image
        x,y=mercator(*centre,z); origin=(x-450+offset[0],y-300+offset[1])
        img,names=self.render(z,origin,900,600,focus=focus) if self.enabled else (Image.new('RGB',(900,600),'white'),set())
        return img,names,origin

def render_tiles(atlas):
    from PIL import Image
    tile_count=0
    for z in range(12,18):
        nw=mercator(BBOX[2],BBOX[1],z); se=mercator(BBOX[0],BBOX[3],z)
        x0,y0=int(nw[0]//256),int(nw[1]//256);x1,y1=int(se[0]//256),int(se[1]//256)
        buffer=128;meta=8
        for mx in range(x0,x1+1,meta):
            for my in range(y0,y1+1,meta):
                nx=min(meta,x1-mx+1);ny=min(meta,y1-my+1)
                im,_=atlas.render(z,(mx*256-buffer,my*256-buffer),nx*256+buffer*2,ny*256+buffer*2)
                for tx in range(nx):
                    out=APP/'tiles'/str(z)/str(mx+tx);out.mkdir(parents=True,exist_ok=True)
                    for ty in range(ny):
                        im.crop((buffer+tx*256,buffer+ty*256,buffer+(tx+1)*256,buffer+(ty+1)*256)).save(out/(str(my+ty)+'.webp'),'WEBP',quality=86,method=3)
                        tile_count+=1
        print('Tiles zoom',z,'total',tile_count,flush=True)
    return tile_count

def save_static(image,qid):
    from PIL import ImageDraw
    draw=ImageDraw.Draw(image)
    draw.rectangle((0,577,900,600),fill='#fffdf8')
    draw.text((12,582),'© OpenStreetMap contributors · ODbL · Original PHV Trainer cartography',font=font(11),fill='#4f5658')
    draw.rounded_rectangle((849,12,887,64),4,fill='#fffdf8',outline='#657479')
    draw.polygon([(868,19),(860,43),(868,38),(876,43)],fill='#263b45');draw.text((863,46),'N',font=font(12,True),fill='#263b45')
    out=APP/'maps/static'/f'{qid}.webp';out.parent.mkdir(parents=True,exist_ok=True);pending=out.with_suffix('.webp.tmp');image.save(pending,'WEBP',quality=82,method=3);pending.replace(out)
    return 'maps/static/'+qid+'.webp'

def make_mcq(data,g,routes,atlas,only=None):
    from PIL import Image,ImageDraw
    rng=random.Random(SEED);bank=[];router=Router(g);count=collections.Counter();allnames=sorted({r['name'] for r in data['roads'] if r['name']}); refroads={};retained_ways={e['osmWay'] for e in g['edges']}
    for r in data['roads']:
        if r['id'] in retained_ways and r['name'] and r['ref'] and re.fullmatch('[AB][0-9]+',r['ref']): refroads.setdefault((r['name'],r['ref']),r)
    def add(section,key,question,correct,distractors,img,evidence,multi=False,marks=None):
        count[key]+=1;qid='TOPO-'+key+'-'+str(count[key]).zfill(3)
        correct=correct if isinstance(correct,list) else [correct]
        options=list(dict.fromkeys(correct+distractors))[:4]
        if len(options)<(2 if key=='ESSENTIALS' else 4): raise ValueError((qid,options))
        rng.shuffle(options);answers=sorted(options.index(c) for c in correct)
        explanation=evidence.pop('explanation')
        item={'id':qid,'type':'multi' if multi else 'mcq','section':section,'question':question+(' Select TWO answers.' if multi else ''),'options':options,'answer':answers if multi else answers[0],'marks':marks or (2 if multi else 1),'explanation':explanation,'difficulty':2 if multi else 1,'map':save_static(img,qid) if atlas.enabled else 'maps/static/'+qid+'.webp','source':SOURCE,'evidence':evidence,'tags':[key.lower()]}
        bank.append(item)
        if len(bank)%25==0:print('Static questions',len(bank),flush=True)
        return item
    def force_label(draw,text,x,y):
        f=font(16,True);b=font_bbox(text,16,True);w=b[2]-b[0];x=max(10,min(880-w,x));y=max(10,min(552,y));draw.rectangle((x-4,y-3,x+w+4,y+21),fill='#fffdf8',outline='#6d6d68');draw.text((x,y),text,font=f,fill='#242e35')
    # Every route-essentials answer follows from the actual drawn path.
    atlas.enabled=not only or 'ESSENTIALS' in only
    closure_routes=[r for r in routes if r['routeType']=='closure'];essential_routes=[r for r in routes if r['routeType']!='long']
    for i in range(70):
        scenario=i%6
        route=closure_routes[(i//6)%len(closure_routes)] if scenario==5 else essential_routes[i%len(essential_routes)]
        p=router.coords(route['unclosedOptimalEdges']) if scenario==5 else route['optimalGeometry'];z=15 if route['routeType']!='long' else 13
        centre=((min(x[0] for x in p)+max(x[0] for x in p))/2,(min(x[1] for x in p)+max(x[1] for x in p))/2)
        while True:
            pixels=[mercator(*x,z) for x in p]
            if max(x[0] for x in pixels)-min(x[0] for x in pixels)<790 and max(x[1] for x in pixels)-min(x[1] for x in pixels)<460:break
            z-=1
        img,names,origin=atlas.static(centre,z);d=ImageDraw.Draw(img)
        pixels=[(x-origin[0],y-origin[1]) for x,y in pixels]
        correct_start=scenario!=0;reverse=scenario==1
        cut=1
        if not correct_start:
            distance_from_start=0
            while cut<len(p)-1:
                distance_from_start+=distance(p[cut-1],p[cut])
                if distance_from_start>=180:break
                cut+=1
        drawn=pixels[cut:] if not correct_start else pixels
        correct_end=scenario!=2
        if not correct_end:
            remaining=0;last=len(p)-1
            while last>1:
                remaining+=distance(p[last-1],p[last]);last-=1
                if remaining>=180:break
            drawn=pixels[:last+1]
        if reverse:drawn=list(reversed(drawn))
        if scenario==5:
            for edgeid in route['closedEdges']:
                edge=router.edges[edgeid];closedpoints=[(x-origin[0],y-origin[1]) for x,y in [mercator(*pt,z) for pt in edge['geometry']]]
                d.line(closedpoints,fill='#e66565',width=12)
            force_label(d,'CLOSED: '+route['closedStreet'],20,20)
        d.line(drawn,fill='#2464ba',width=6,joint='curve')
        for j in range(1,len(drawn),max(1,len(drawn)//7)):Atlas.arrow(d,drawn[j-1],drawn[j],'#164b98',20)
        for point,color,text in ((pixels[0],'#21834c','START'),(pixels[-1],'#c83e45','END')):
            x,y=point;d.ellipse((x-9,y-9,x+9,y+9),fill=color,outline='white',width=2);force_label(d,text,x+13,y-22)
        if scenario==0:
            q='The blue route begins at the green start marker. Is this statement true or false?';truth=correct_start;reason='The blue line begins after the start marker, so its starting point is incorrect.'
        elif scenario==1:
            q='The blue arrows travel from the green start to the red destination. Is this statement true or false?';truth=False;reason='The arrows run from the destination towards the start: the route is reversed.'
        elif scenario==2:
            q='The blue route finishes at the red destination marker. Is this statement true or false?';truth=False;reason='The blue route stops at least 180 metres before the destination marker.'
        elif scenario==3:
            q='The blue route is the shortest legal route in this exercise. Is this statement true or false?';truth=True;reason=f'The blue route follows the computed shortest permitted path ({route["optimalLength"]/1000:.2f} km), including the represented turn and access restrictions.'
        elif scenario==5:
            q='The blue route avoids the street marked CLOSED. Is this statement true or false?';truth=False;reason=f'The blue route uses {route["closedStreet"]}. The red closure applies even if that street would otherwise give a shorter journey.'
        else:
            q='The route is shown in the required start-to-destination direction. Is this statement true or false?';truth=True;reason='The arrows begin at the green start and finish at the red destination.'
        q=f'For the journey from {route["startName"]} to {route["endName"]}: '+q
        add('Route planning essentials','ESSENTIALS',q,'True' if truth else 'False',['False' if truth else 'True'],img,{'kind':'route_scenario','scenario':scenario,'routeId':route['id'],'startCorrect':correct_start,'endCorrect':correct_end,'reverse':reverse,'truth':truth,'drawnEdges':route['unclosedOptimalEdges'] if scenario==5 else route['optimalEdges'],'explanation':reason})
    # Symbols at real OSM locations; coloured initials are explained in legend.
    atlas.enabled=not only or 'SYMBOL' in only
    ps=list(g['pois']);rng.shuffle(ps)
    for i,p in enumerate(ps[:60]):
        img,names,origin=atlas.static((p['lat'],p['lng']),16,offset=(150,-70),focus=True);d=ImageDraw.Draw(img);x,y=mercator(p['lat'],p['lng'],16);x-=origin[0];y-=origin[1];Atlas.symbol(d,p['category'],x,y,13);d.ellipse((x-24,y-24,x+24,y+24),outline='#c72e3f',width=4)
        add('Map symbols','SYMBOL',f'What does the symbol circled in red near {p["name"]} represent?',CATEGORIES[p['category']],[v for k,v in CATEGORIES.items() if k!=p['category']][:3],img,{'kind':'symbol','poi':p['id'],'category':p['category'],'explanation':f'The circled {SYMBOLS[p["category"]]} symbol is the atlas symbol for a {CATEGORIES[p["category"]].lower()}. OSM identifies this feature as {p["category"]}.'})
    # POIs: distractors are real names from the same category, outside the crop.
    atlas.enabled=not only or 'POI' in only
    suitable=[p for p in ps if len({x['name'] for x in ps if x['category']==p['category']})>=5]
    for i,p in enumerate(suitable[:70]):
        img,names,origin=atlas.static((p['lat'],p['lng']),17,offset=(140,-50),focus=True);d=ImageDraw.Draw(img);x,y=mercator(p['lat'],p['lng'],17);x-=origin[0];y-=origin[1];Atlas.symbol(d,p['category'],x,y,13);d.ellipse((x-23,y-23,x+23,y+23),outline='#c72e3f',width=3);force_label(d,p['name'],x+28,y-10)
        distractors=[x['name'] for x in ps if x['category']==p['category'] and x['name']!=p['name'] and distance((x['lat'],x['lng']),(p['lat'],p['lng']))>1500]
        if len(distractors)<3:raise ValueError('POI distractor shortage')
        add('Places of interest','POI',f'Look at the map. Which {CATEGORIES[p["category"]].lower()} is circled in red?',p['name'],distractors[:3],img,{'kind':'poi','poi':p['id'],'category':p['category'],'name':p['name'],'explanation':f'The label next to the circled {CATEGORIES[p["category"]].lower()} reads {p["name"]}. The name and location come from OSM {p["osmType"]} {p["osmId"]}.'})
    # 70 street-identification items: 50 dual-answer items, 20 single-answer.
    atlas.enabled=not only or 'STREET' in only
    named=[r for r in data['roads'] if r['id'] in retained_ways and r['name'] and len(r['geometry'])>1];rng.shuffle(named);seen_streets=set()
    for r in named:
        if count['STREET']>=70:break
        if r['name'] in seen_streets:continue
        p=r['geometry'][len(r['geometry'])//2];img,names,origin=atlas.static(p,17,focus=True);d=ImageDraw.Draw(img)
        nearby=[x for x in named if x['name']!=r['name'] and distance(p,x['geometry'][0])<220]
        if not nearby:continue
        second=nearby[0];multi=count['STREET']<50;correct=[r['name'],second['name']] if multi else [r['name']]
        for k,road in enumerate([r,second] if multi else [r]):
            point=road['geometry'][len(road['geometry'])//2];px,py=mercator(*point,17);px-=origin[0];py-=origin[1];force_label(d,road['name'].upper(),px+8,py+24*k)
        # Exclude every geographically present road, not only rendered labels.
        road_features,road_tree=atlas.at_zoom(17)['roads']
        present={road_features[int(idx)][0]['name'] for idx in road_tree.query(atlas.box(origin[0]-70,origin[1]-70,origin[0]+970,origin[1]+670))}
        distractors=[n for n in allnames if n not in present and n not in correct];rng.shuffle(distractors)
        add('Specific streets','STREET',('Which of the following streets are labelled on this map?' if multi else 'Which of the following streets is labelled on this map?')+f' Use extract {count["STREET"]+1}.',correct,distractors[:4-len(correct)],img,{'kind':'streets','visible':correct,'wayIds':[r['id'],second['id']] if multi else [r['id']],'explanation':'The map labels '+ ' and '.join(correct)+'. The other options are real streets outside this extract.'},multi)
        seen_streets.add(r['name'])
    # Road numbers: distinct streets and referenced OSM ways. 30 dual-answer.
    atlas.enabled=not only or 'ROADNO' in only
    refs=list(refroads.values());rng.shuffle(refs)
    if len(refs)<60:raise ValueError(('Need 60 named numbered roads',len(refs)))
    for i,r in enumerate(refs[:60]):
        p=r['geometry'][len(r['geometry'])//2];other=None
        multi=i<30
        if multi:
            nearby=sorted([x for x in refs if x['name']!=r['name'] and x['ref']!=r['ref']],key=lambda x:distance(p,x['geometry'][len(x['geometry'])//2]))
            other=nearby[0];op=other['geometry'][len(other['geometry'])//2];centre=((p[0]+op[0])/2,(p[1]+op[1])/2);z=16
            while distance(p,op)>900*2**(16-z):z-=1
            img,names,origin=atlas.static(centre,z,focus=True);d=ImageDraw.Draw(img)
            force_label(d,r['name'].upper()+'  '+r['ref'],90,70);force_label(d,other['name'].upper()+'  '+other['ref'],380,440)
            correct=[f'{r["name"]} — {r["ref"]}',f'{other["name"]} — {other["ref"]}'];wrong=[f'{r["name"]} — {other["ref"]}',f'{other["name"]} — {r["ref"]}']
            q=f'Use the two highlighted labels near {r["name"]}. Which road-number pairs match the map?'
        else:
            img,names,origin=atlas.static(p,16,focus=True);d=ImageDraw.Draw(img);force_label(d,r['name'].upper()+'  '+r['ref'],190,70)
            correct=[r['ref']];wrong=list(dict.fromkeys(x['ref'] for x in refs if x['ref']!=r['ref']))[:3];q=f'What road number is shown for {r["name"]}?'
        pair=[{'way':x['id'],'name':x['name'],'ref':x['ref']} for x in ([r,other] if other else [r])]
        reason='; '.join(x['name']+' is labelled '+x['ref'] for x in pair)+'. These name/reference pairs come from the original OSM ways.'
        add('Road numbers','ROADNO',q,correct,wrong,img,{'kind':'road_number','way':r['id'],'name':r['name'],'ref':r['ref'],'roads':pair,'explanation':reason},multi)
    # Compass grids are computed illustrations, not London road claims.
    atlas.enabled=not only or 'COMPASS' in only
    seen=set()
    for i in range(40):
        img=Image.new('RGB',(900,600),'#fffdf6');d=ImageDraw.Draw(img);n=5;coords={r*5+c+1:(220+c*115,70+r*100) for r in range(5) for c in range(5)}
        for r in range(5):d.line([coords[r*5+1],coords[r*5+5]],fill='#b6c2ca',width=13)
        for c in range(5):d.line([coords[c+1],coords[21+c]],fill='#b6c2ca',width=13)
        for num,(x,y) in coords.items():d.ellipse((x-18,y-18,x+18,y+18),fill='#fff',outline='#253f58',width=2);d.text((x-8,y-10),str(num),font=font(17,True),fill='#253f58')
        while True:
            row,col=rng.randrange(5),rng.randrange(5);dr,dc=rng.choice([-2,-1,1,2]),rng.choice([-2,-1,1,2])
            if 0<=row+dr<5 and 0<=col+dc<5 and (row,col,dr,dc) not in seen:break
        seen.add((row,col,dr,dc));start=row*5+col+1;end=(row+dr)*5+col+dc+1
        q=f'Starting from junction {start}, travel {abs(dc)} street'+('s' if abs(dc)!=1 else '')+(' east' if dc>0 else ' west')+f' and {abs(dr)} street'+('s' if abs(dr)!=1 else '')+(' south' if dr>0 else ' north')+'. At which junction do you arrive?'
        wrong=[str(x) for x in (end-1,end+1,end-5,end+5,1,25) if 1<=x<=25 and x!=end][:3]
        add('Compass points and directions','COMPASS',q,str(end),wrong,img,{'kind':'grid','gridSize':5,'start':start,'east':dc,'south':dr,'end':end,'explanation':f'On this north-up grid, the destination is row {row+dr+1}, column {col+dc+1}: junction {end}.'})
    # 30 geographically computed travel bearings, only within 15 degrees of a
    # compass octant. 20 are dual statement questions.
    directions=['North','North-east','East','South-east','South','South-west','West','North-west'];used=set()
    for e in g['edges']:
        if count['COMPASS']>=70:break
        if not e['name'] or e['name'] in used or e['length']<40:continue
        a,b=e['geometry'][0],e['geometry'][-1];dy=b[0]-a[0];dx=(b[1]-a[1])*math.cos(math.radians((a[0]+b[0])/2));bearing=(math.degrees(math.atan2(dx,dy))+360)%360;k=round(bearing/45)%8;error=abs((bearing-k*45+180)%360-180)
        if error>15:continue
        centre=((a[0]+b[0])/2,(a[1]+b[1])/2);img,names,origin=atlas.static(centre,17,focus=True);d=ImageDraw.Draw(img);pixels=[(x-origin[0],y-origin[1]) for x,y in [mercator(*p,17) for p in e['geometry']]];d.line(pixels,fill='#2464ba',width=7);Atlas.arrow(d,pixels[0],pixels[-1],'#163875',30);force_label(d,e['name'].upper(),200,70)
        multi=count['COMPASS']<60;correct=[directions[k]];wrong=[directions[(k+j)%8] for j in (2,4,6)]
        q=f'In which compass direction does the blue arrow travel along {e["name"]}?'
        if multi:
            correct=[f'The arrow points approximately {directions[k].lower()}.',f'The opposite direction is {directions[(k+4)%8].lower()}.'];wrong=[f'The arrow points approximately {directions[(k+2)%8].lower()}.',f'The opposite direction is {directions[k].lower()}.'];q=f'Which statements describe the blue arrow on {e["name"]}?'
        add('Compass points and directions','COMPASS',q,correct,wrong,img,{'kind':'bearing','edge':e['id'],'bearing':round(bearing,2),'direction':directions[k],'explanation':f'The arrow follows OSM way {e["osmWay"]} with a bearing of {bearing:.1f}°. This is within 15° of {directions[k].lower()}.'},multi);used.add(e['name'])
    print('MCQ bank',dict(count), 'multi',sum(x['type']=='multi' for x in bank),flush=True)
    if len(bank)!=400:raise RuntimeError(('MCQ targets not met',dict(count)))
    return bank

def legend():
    from PIL import Image,ImageDraw
    img=Image.new('RGB',(900,760),'#fffdf6');d=ImageDraw.Draw(img);d.text((35,25),'MAP REFERENCE PAGE',font=font(27,True),fill='#173e66');d.text((35,68),'Original atlas symbols · North is at the top of static maps',font=font(16),fill='#51616f')
    for i,(cat,title) in enumerate(CATEGORIES.items()):
        col=i//6;row=i%6;x=60+col*430;y=130+row*65;Atlas.symbol(d,cat,x,y,13);d.text((x+28,y-12),title,font=font(18),fill='#25333e')
    d.line((40,555,140,555),fill='#615f58',width=14);d.line((40,555,140,555),fill='#f4cc69',width=10);d.text((155,544),'Main road / road number e.g. A501',font=font(16),fill='#25333e')
    d.line((40,598,140,598),fill='#615f58',width=11);d.line((40,598,140,598),fill='#fffaf4',width=7);d.text((155,587),'Minor street',font=font(16),fill='#25333e')
    d.rectangle((535,540,575,565),fill='#c6dcae');d.text((590,542),'Park / garden',font=font(15),fill='#25333e')
    d.rectangle((535,585,575,610),fill='#acd6df');d.text((590,587),'Water',font=font(15),fill='#25333e')
    Atlas.arrow(d,(40,645),(140,645),'#263e4a',30);d.text((155,634),'One-way arrow: travel only in this direction',font=font(16),fill='#25333e')
    d.ellipse((52,684,74,706),fill='white',outline='#bc2f3f',width=3);d.line((56,702,70,688),fill='#bc2f3f',width=3);d.text((155,681),'Restricted turn: select the marker for its movement',font=font(16),fill='#25333e')
    d.text((35,730),'© OpenStreetMap contributors · Database ODbL-1.0 · Not a navigation map',font=font(12),fill='#59636a');out=APP/'maps/legend.webp';out.parent.mkdir(parents=True,exist_ok=True);img.save(out,'WEBP',quality=92)
    empty=Image.new('RGB',(256,256),'#edeae3');ed=ImageDraw.Draw(empty);ed.text((25,112),'Outside practice coverage',font=font(13),fill='#687578');(APP/'tiles').mkdir(parents=True,exist_ok=True);empty.save(APP/'tiles/empty.webp','WEBP',quality=80)

def subgraphs(g,routes):
    out=APP/'data/topo_routes';out.mkdir(parents=True,exist_ok=True)
    nodes={n['id']:n for n in g['nodes']}
    for r in routes:
        s,w=r['bounds'][0];n,e=r['bounds'][1];padlat=800/111195;padlon=800/(111195*math.cos(math.radians((s+n)/2)))
        chosen=[x for x in g['edges'] if any(s-padlat<=p[0]<=n+padlat and w-padlon<=p[1]<=e+padlon for p in x['geometry'])];ids={x['id'] for x in chosen};ns={k for x in chosen for k in (x['from'],x['to'])}
        # Compact reference subset. Geometry lives once in map_data.js, avoiding
        # a hundred copies of central London's roads in the published bundle.
        subset={'id':r['id'],'nodeIds':sorted(ns),'edgeIds':sorted(ids),'restrictions':[x for x in g['restrictions'] if x['fromEdge'] in ids and x['toEdge'] in ids]}
        text='window.TOPO_ROUTES=window.TOPO_ROUTES||{};window.TOPO_ROUTES['+json.dumps(r['id'])+']='+json.dumps(subset,separators=(',',':'))+';\n';(out/(r['id']+'.js')).write_text(text,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--extract',action='store_true');parser.add_argument('--areas',action='store_true');parser.add_argument('--tiles',action='store_true');parser.add_argument('--bank',action='store_true');parser.add_argument('--only',help='Render selected MCQ groups; existing other images are retained');args=parser.parse_args();WORK.mkdir(parents=True,exist_ok=True)
    data=extract() if args.extract or not ((WORK/'extracted.json').exists() or (WORK/'extracted.json.gz').exists()) else cache_read('extracted.json')
    if args.areas and not data.get('areaRelationsExtracted'):data=extract_areas(data)
    if not ((WORK/'graph.json').exists() or (WORK/'graph.json.gz').exists()) or args.extract:
        g=graph(data);cache_write('graph.json',g)
    else:g=cache_read('graph.json')
    if args.extract or not (APP/'data/map_data.js').exists():dump_js(APP/'data/map_data.js','PHV_MAP',g)
    if not ((WORK/'routes.json').exists() or (WORK/'routes.json.gz').exists()) or args.extract:
        routes=make_routes(g);cache_write('routes.json',routes)
    else:routes=cache_read('routes.json')
    router=Router(g)
    for route in routes:route['directions']=turn_instructions(route['optimalEdges'],router)
    if args.extract or not all((APP/'data/topo_routes'/(r['id']+'.js')).exists() for r in routes):subgraphs(g,routes)
    if not args.bank or not (APP/'data/topo_bank.js').exists():dump_js(APP/'data/topo_bank.js','TOPO_BANK',routes)
    atlas=Atlas(data,g)
    if args.tiles:render_tiles(atlas)
    if args.bank:
        bank=make_mcq(data,g,routes,atlas,args.only.split(',') if args.only else None);dump_js(APP/'data/topo_bank.js','TOPO_BANK',bank+routes)
    legend()
    pbf=WORK/'greater-london-latest.osm.pbf';hashcache=WORK/'pbf-sha256.txt'
    if pbf.exists():
        digest=hashlib.sha256(pbf.read_bytes()).hexdigest();hashcache.write_text(digest,encoding='ascii')
    else:digest=hashcache.read_text(encoding='ascii').strip()
    manifest={'pbfSha256':digest,'source':SOURCE,'accessed':g.get('accessed',DATE),'bounds':BBOX,'nodes':len(g['nodes']),'edges':len(g['edges']),'restrictions':len(g['restrictions']),'unsupportedRestrictionCount':len(g.get('unsupportedRestrictions',[])),'pois':len(g['pois']),'routes':len(routes),'tileCount':len(list((APP/'tiles').rglob('*.webp'))),'staticImageCount':len(list((APP/'maps/static').glob('*.webp')))}
    (APP/'data/map_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('Done',manifest,flush=True)

if __name__=='__main__':main()
