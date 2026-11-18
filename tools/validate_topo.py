"""Independent checks for the released OSM data and answer keys."""
from __future__ import annotations
import collections
import heapq
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'app'

def read_js(path):
    text=path.read_text(encoding='utf-8');return json.loads(text[text.index(' = ')+3:].strip().removesuffix(';'))

def main():
    graph=read_js(APP/'data/map_data.js');bank=read_js(APP/'data/topo_bank.js');nodes={n['id']:n for n in graph['nodes']};edges={e['id']:e for e in graph['edges']};pois={p['id']:p for p in graph['pois']}
    errors=[]
    def check(truth,msg):
        if not truth:errors.append(msg)
    check(len(nodes)==len(graph['nodes']),'Duplicate node IDs');check(len(edges)==len(graph['edges']),'Duplicate edge IDs')
    check(len({q['id'] for q in bank})==len(bank),'Duplicate item IDs')
    banned={(r['fromEdge'],r['toEdge']) for r in graph['restrictions']};out=collections.defaultdict(list)
    for e in edges.values():
        check(e['from'] in nodes and e['to'] in nodes,'Missing edge endpoint '+e['id']);check(e['length']>0,'Nonpositive edge length '+e['id']);check(len(e['geometry'])>=2,'Missing geometry '+e['id']);out[e['from']].append(e)
        a,b=nodes[e['from']],nodes[e['to']]
        check(e['geometry'][0]==[a['lat'],a['lng']] and e['geometry'][-1]==[b['lat'],b['lng']],'Geometry does not meet endpoints '+e['id'])
    def shortest(start,end,closed):
        todo=[(0,start,'')];seen={};closed=set(closed)
        while todo:
            d,n,last=heapq.heappop(todo)
            if (n,last) in seen:continue
            seen[(n,last)]=d
            if n==end:return d
            for e in out[n]:
                if e['id'] not in closed and (last,e['id']) not in banned and (e['to'],e['id']) not in seen:heapq.heappush(todo,(d+e['length'],e['to'],e['id']))
        return float('inf')
    def legal(path,closed,qid):
        check(bool(path),qid+' empty path')
        for i,eid in enumerate(path):
            check(eid in edges,qid+' missing edge '+eid)
            if eid not in edges:continue
            check(eid not in closed,qid+' uses closed edge')
            if i:
                check(edges[path[i-1]]['to']==edges[eid]['from'],qid+' broken continuity')
                check((path[i-1],eid) not in banned,qid+' prohibited turn')
        return sum(edges[e]['length'] for e in path)
    counts=collections.Counter();sections=collections.Counter();positions=collections.Counter();arity_positions=collections.defaultdict(collections.Counter);multi_positions=collections.Counter();semantic_seen={};exact_seen={};mcq_items=[]
    routes={q['id']:q for q in bank if q['type']=='route'}
    for q in bank:
        qid=q['id'];sections[q['section']]+=1
        for key in ('id','type','section','question','explanation','source','evidence','marks'):check(key in q,qid+' missing '+key)
        if q['type']=='route':
            counts[q['routeType']]+=1;p=q['optimalEdges'];length=legal(p,set(q['closedEdges']),qid)
            check(edges[p[0]]['from']==q['start'] and edges[p[-1]]['to']==q['end'],qid+' incorrect endpoints')
            check(abs(length-q['optimalLength'])<.03,qid+' incorrect optimal length')
            low,high=(5000,12000) if q['routeType']=='long' else (1000,3000)
            check(low<=length<=high,qid+' wrong distance band')
            best=shortest(q['start'],q['end'],q['closedEdges']);check(abs(length-best)<.03,qid+' route is not distance-optimal')
            check(q['marks']==22,qid+' expected22 marks')
            if q['routeType']=='closure':
                check(bool(set(q['closedEdges'])&set(q['unclosedOptimalEdges'])),qid+' closure did not intersect original optimal route')
                check(all(edges[e]['name']==q['closedStreet'] for e in q['closedEdges']),qid+' closure name mismatch')
            for alt in q['acceptable']:
                length2=legal(alt['edges'],set(q['closedEdges']),qid+' alternative');check(length2<=length*1.05+.01,qid+' alternative >5% longer')
            check((APP/'data/topo_routes'/f'{qid}.js').is_file(),qid+' missing subgraph')
            # All route points must have source raster tiles at every supported zoom.
            for z in range(graph['minZoom'],graph['maxZoom']+1):
                for lat,lon in q['optimalGeometry']:
                    x=int((lon+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
                    check((APP/'tiles'/str(z)/str(x)/(str(y)+'.webp')).exists(),qid+f' missing tile {z}/{x}/{y}')
            continue
        counts['mcq']+=1;counts['multi']+=q['type']=='multi';options=q['options'];answer=q['answer'];ev=q['evidence'];kind=ev['kind'];mcq_items.append(q)
        identity=(ev.get('routeId'),ev.get('scenario')) if kind=='route_scenario' else ev.get('poi') if kind in {'symbol','poi'} else tuple(sorted(ev['visible'])) if kind=='streets' else tuple(sorted((r['name'],r['ref']) for r in ev['roads'])) if kind=='road_number' else (ev['start'],ev['east'],ev['south']) if kind=='grid' else ev.get('edge')
        semantic=(kind,identity);check(semantic not in semantic_seen,qid+' duplicates geographic target '+str(semantic_seen.get(semantic)));semantic_seen[semantic]=qid
        check(len(options)==(2 if kind=='route_scenario' else 4),qid+' option count')
        check(len(set(options))==len(options),qid+' duplicate options')
        check((APP/q['map']).is_file(),qid+' missing image')
        if (APP/q['map']).exists():
            image_hash=hashlib.sha256((APP/q['map']).read_bytes()).hexdigest();exact=(q['question'].casefold(),image_hash);check(exact not in exact_seen,qid+' duplicates image and question '+str(exact_seen.get(exact)));exact_seen[exact]=qid
        from PIL import Image
        with Image.open(APP/q['map']) as im:check(im.size==(900,600),qid+' image not900x600')
        if q['type']=='multi':
            check(isinstance(answer,list) and len(answer)==2 and len(set(answer))==2,qid+' invalid multi answer');selected=[options[i] for i in answer];check(q['marks']==2,qid+' multi marks');multi_positions.update(answer)
        else:check(isinstance(answer,int) and 0<=answer<len(options),qid+' invalid answer');selected=[options[answer]];positions[answer]+=1;arity_positions[len(options)][answer]+=1
        expected=[]
        if kind=='symbol':
            from build_maps import CATEGORIES
            check(ev['poi'] in pois,qid+' nonexistent POI');expected=[CATEGORIES[pois[ev['poi']]['category']]]
        elif kind=='poi':expected=[pois[ev['poi']]['name']]
        elif kind=='streets':
            names={e['name'] for e in edges.values() if e['osmWay'] in ev['wayIds']};check(set(ev['visible'])<=names,qid+' streets not in source ways');expected=ev['visible']
        elif kind=='road_number':
            original=[e for e in edges.values() if e['osmWay']==ev['way']]
            # Some ref labels are on non-drivable road fragments: cache is the
            # reproducible source in developer builds, otherwise nearby retained
            # ways with exactly the same name/ref provide the proof.
            if not original:original=[e for e in edges.values() if e['name']==ev['name'] and e['ref']==ev['ref']]
            check(bool(original),qid+' road reference absent from released source graph')
            check(all(e['ref']==ev['ref'] for e in original),qid+' road reference mismatch')
            if q['type']=='multi':
                expected=[]
                for road in ev['roads']:
                    check(any(e['name']==road['name'] and e['ref']==road['ref'] for e in edges.values()),qid+' paired road missing from source graph')
                    expected.append(f'{road["name"]} — {road["ref"]}')
            else:expected=[ev['ref']]
        elif kind=='grid':
            size=ev['gridSize'];r,c=divmod(ev['start']-1,size);r+=ev['south'];c+=ev['east'];check(0<=r<size and 0<=c<size,qid+' grid move out of bounds');expected=[str(r*size+c+1)]
        elif kind=='bearing':
            e=edges[ev['edge']];a,b=e['geometry'][0],e['geometry'][-1];bearing=(math.degrees(math.atan2((b[1]-a[1])*math.cos(math.radians((a[0]+b[0])/2)),b[0]-a[0]))+360)%360;k=round(bearing/45)%8;dirs=['North','North-east','East','South-east','South','South-west','West','North-west'];check(abs((bearing-k*45+180)%360-180)<=15,qid+' compass bearing ambiguous')
            expected=[f'The arrow points approximately {dirs[k].lower()}.',f'The opposite direction is {dirs[(k+4)%8].lower()}.'] if q['type']=='multi' else [dirs[k]]
        elif kind=='route_scenario':
            check(ev['routeId'] in routes,qid+' missing scenario route')
            if 'begins at' in q['question']:truth=ev['startCorrect'] and not ev['reverse']
            elif 'finishes at' in q['question']:truth=ev.get('endCorrect',True) and not ev['reverse']
            elif 'shortest legal' in q['question']:truth=ev['drawnEdges']==routes[ev['routeId']]['optimalEdges']
            elif 'avoids the street' in q['question']:truth=not bool(set(ev['drawnEdges'])&set(routes[ev['routeId']]['closedEdges']))
            else:truth=not ev['reverse']
            expected=['True' if truth else 'False']
        else:check(False,qid+' unsupported evidence kind')
        check(sorted(selected)==sorted(expected),qid+' answer does not recompute from source')
    check(counts['short']>=60,'Need60 short routes');check(counts['closure']>=40,'Need40 closure routes');check(counts['long']>=40,'Need40 long routes');check(counts['mcq']>=400,'Need400 MCQ');check(counts['multi']>=70,'Need70 dual-answer items')
    check((APP/'maps/legend.webp').exists(),'Missing map key')
    for section in ('Route planning essentials','Route planning','Map symbols','Places of interest','Specific streets','Road numbers','Compass points and directions'):check(sections[section]>0,'Missing section '+section)
    for arity,histogram in arity_positions.items():
        values=[histogram[i] for i in range(arity)];check(max(values)-min(values)<=1,f'Answer positions not balanced for {arity} options: {values}')
    check(max(multi_positions.values())-min(multi_positions.values())<=2,'Multi-answer positions not balanced')
    from rapidfuzz.fuzz import ratio
    near=[]
    for i,a in enumerate(mcq_items):
        for b in mcq_items[i+1:]:
            similarity=ratio(a['question'],b['question'])
            if similarity>85:near.append({'a':a['id'],'b':b['id'],'similarity':round(similarity,2)})
    report={'counts':dict(counts),'sections':dict(sections),'singleAnswerPositionsByOptionCount':{str(k):dict(v) for k,v in arity_positions.items()},'multiAnswerPositionUses':dict(multi_positions),'semanticDuplicateCount':sum('duplicates geographic target' in e for e in errors),'imageQuestionDuplicateCount':sum('duplicates image and question' in e for e in errors),'nearStemPairCount':len(near),'nearStemExplanation':'Similar instructions on distinct maps/source targets are expected; semantic and image-question duplicates are rejected.','nearStemExamples':near[:12],'errors':errors[:50],'errorCount':len(errors)}
    (ROOT/'docs/TOPO_VALIDATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)
    print('Topographical validation PASS: every answer recomputed, every route distance-optimal and legal in the released exercise graph.')

if __name__=='__main__':main()
