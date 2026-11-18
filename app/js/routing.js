(function () {
  'use strict';
  const R=6371000, rad=Math.PI/180;
  let built=null;
  function distance(a,b){const dy=(b[0]-a[0])*rad,dx=(b[1]-a[1])*rad;const h=Math.sin(dy/2)**2+Math.cos(a[0]*rad)*Math.cos(b[0]*rad)*Math.sin(dx/2)**2;return 2*R*Math.atan2(Math.sqrt(h),Math.sqrt(Math.max(0,1-h)));}
  function coord(n){return [n.lat,n.lng];}
  function graph(){
    if(built)return built;
    const data=window.PHV_MAP||{nodes:[],edges:[],restrictions:[]}, nodes=new Map(data.nodes.map(n=>[String(n.id),n])), edges=new Map(),adj=new Map(), physical=new Map(), pieces=[], pairs=new Set();
    function put(map,id,e){if(!map.has(id))map.set(id,[]);map.get(id).push(e);}
    for(const raw of data.edges){
      const e=Object.assign({},raw,{id:String(raw.id),from:String(raw.from),to:String(raw.to)});e.geometry=e.geometry||[coord(nodes.get(e.from)),coord(nodes.get(e.to))];edges.set(e.id,e);
      const ids=e.geometry.map((p,i)=>{if(i===0)return e.from;if(i===e.geometry.length-1)return e.to;const id='@'+(e.osmWay||[e.from,e.to].sort().join(':'))+':'+p.join(',');if(!nodes.has(id))nodes.set(id,{id,lat:p[0],lng:p[1]});return id;});
      const lengths=e.geometry.slice(1).map((p,i)=>distance(e.geometry[i],p)),sum=lengths.reduce((a,b)=>a+b,0);
      for(let i=1;i<ids.length;i++){const piece=Object.assign({},e,{id:e.id+'@'+i,parentId:e.id,from:ids[i-1],to:ids[i],length:sum?e.length*lengths[i-1]/sum:0,geometry:[e.geometry[i-1],e.geometry[i]]});pieces.push(piece);pairs.add(piece.from+'|'+piece.to);put(adj,piece.from,piece);put(physical,piece.from,piece);}
    }
    for(const e of pieces)if(!pairs.has(e.to+'|'+e.from)){put(physical,e.to,Object.assign({},e,{id:e.id+'~reverse',originalId:e.parentId,from:e.to,to:e.from,geometry:e.geometry.slice().reverse(),wrongWay:true}));}
    const banned=new Set();for(const r of data.restrictions||[])banned.add(String(r.fromEdge)+'|'+String(r.toEdge));
    const spatial=new Map();for(const n of nodes.values()){const key=Math.floor(n.lat/.0005)+','+Math.floor(n.lng/.0005);if(!spatial.has(key))spatial.set(key,[]);spatial.get(key).push(n);}
    built={nodes,edges,adj,physical,banned,spatial};return built;
  }
  class Heap {constructor(){this.a=[];}push(v){let i=this.a.length;this.a.push(v);while(i>0){const p=(i-1)>>1;if(this.a[p][0]<=v[0])break;this.a[i]=this.a[p];i=p;}this.a[i]=v;}pop(){const top=this.a[0],last=this.a.pop();if(this.a.length){let i=0;while(i*2+1<this.a.length){let j=i*2+1;if(j+1<this.a.length&&this.a[j+1][0]<this.a[j][0])j++;if(last[0]<=this.a[j][0])break;this.a[i]=this.a[j];i=j;}this.a[i]=last;}return top;}get size(){return this.a.length;}}
  function nearest(p){let best=null,d=Infinity;const g=graph(),y=Math.floor(p[0]/.0005),x=Math.floor(p[1]/.0005);for(let dy=-4;dy<=4;dy++)for(let dx=-6;dx<=6;dx++)for(const n of g.spatial.get((y+dy)+','+(x+dx))||[]){const nd=distance(p,coord(n));if(nd<d){d=nd;best=n;}}if(!best)for(const n of g.nodes.values()){const nd=distance(p,coord(n));if(nd<d){d=nd;best=n;}}return {node:best,distance:d};}
  function segmentDistance(p,a,b){const cos=Math.cos((a[0]+b[0])*rad/2),x=(p[1]-a[1])*rad*R*cos,y=(p[0]-a[0])*rad*R,dx=(b[1]-a[1])*rad*R*cos,dy=(b[0]-a[0])*rad*R;const t=Math.max(0,Math.min(1,(x*dx+y*dy)/(dx*dx+dy*dy||1)));return Math.hypot(x-t*dx,y-t*dy);}
  function path(from,to,options){
    const opt=options||{},g=graph(),adj=opt.physical?g.physical:g.adj,closed=new Set((opt.closedEdges||[]).map(String));
    from=String(from);to=String(to);if(from===to)return [];
    const heap=new Heap(),best=new Map(),prev=new Map();const first=from+'|';best.set(first,0);heap.push([0,first,from,'']);let finish=null,visits=0;
    while(heap.size&&visits++<100000){const [cost,key,node,last]=heap.pop();if(cost!==best.get(key))continue;if(node===to){finish=key;break;}
      for(const e of adj.get(node)||[]){const parent=e.parentId||e.id;if(!opt.physical&&(closed.has(parent)||g.banned.has(last+'|'+parent)))continue;if(opt.allow&&!opt.allow(e))continue;const next=e.to+'|'+parent,nc=cost+e.length;if(nc<(best.get(next)??Infinity)){best.set(next,nc);prev.set(next,[key,e]);heap.push([nc,next,e.to,parent]);}}
    }
    if(!finish)return null;const route=[];while(prev.has(finish)){const p=prev.get(finish);route.push(p[1]);finish=p[0];}return route.reverse();
  }
  function geometry(edges){const pts=[];edges.forEach(e=>e.geometry.forEach(p=>{if(!pts.length||distance(p,pts[pts.length-1])>.1)pts.push(p);}));return pts;}
  function optimalEdges(q){return (q.optimalEdges||[]).map(id=>graph().edges.get(String(id))).filter(Boolean);}
  function optimalPoints(q){const e=optimalEdges(q);return e.length?geometry(e):(q.optimal||[]).map(id=>graph().nodes.get(String(id))).filter(Boolean).map(coord);}
  function streetList(edges){const names=[];for(const e of edges){const name=e.name||e.ref||'Unnamed road';if(names[names.length-1]!==name)names.push(name);}return names;}
  // Recognise a drawing following a known legal route, with only screen-pixel
  // tolerance. Samples must advance continuously along its entire geometry;
  // sharing endpoints, cutting a corner or tracing it backwards is insufficient.
  function followsReference(points,reference,tolerance){
    if(reference.length<2||distance(points[0],reference[0])>tolerance||distance(points[points.length-1],reference[reference.length-1])>tolerance)return false;
    const origin=reference[0],cos=Math.cos(origin[0]*rad),xy=p=>[(p[1]-origin[1])*rad*R*cos,(p[0]-origin[0])*rad*R];
    const ref=reference.map(xy),drawn=points.map(xy),segments=[];let total=0;
    for(let i=1;i<ref.length;i++){const a=ref[i-1],b=ref[i],length=Math.hypot(b[0]-a[0],b[1]-a[1]);if(length>.001){segments.push({a,b,length,start:total});total+=length;}}
    let progress=0,index=0;
    for(let i=1;i<drawn.length;i++){const a=drawn[i-1],b=drawn[i],length=Math.hypot(b[0]-a[0],b[1]-a[1]),samples=Math.max(1,Math.ceil(length/2)),step=length/samples;
      for(let j=1;j<=samples;j++){const p=[a[0]+(b[0]-a[0])*j/samples,a[1]+(b[1]-a[1])*j/samples];while(index<segments.length-1&&segments[index].start+segments[index].length<progress-tolerance)index++;let best=null,bestScore=Infinity;
        for(let k=index;k<segments.length&&segments[k].start<=progress+step+2*tolerance+2;k++){const s=segments[k],dx=s.b[0]-s.a[0],dy=s.b[1]-s.a[1],t=Math.max(0,Math.min(1,((p[0]-s.a[0])*dx+(p[1]-s.a[1])*dy)/(s.length*s.length))),station=s.start+t*s.length,d=Math.hypot(p[0]-s.a[0]-t*dx,p[1]-s.a[1]-t*dy);if(station<progress-tolerance||station>progress+step+2*tolerance+2)continue;const score=d*d+.0001*(station-progress-step)**2;if(d<=tolerance&&score<bestScore){bestScore=score;best=station;}}
        if(best===null)return false;progress=Math.max(progress,best);
      }
    }
    return total-progress<=tolerance;
  }
  function grade(q,points,total){
    const g=graph(),cfg=window.PHV_CONFIG.marking,start=g.nodes.get(String(q.start)),end=g.nodes.get(String(q.end));
    const result={score:0,total,correct:false,details:[],violations:[],matched:[],streets:[],length:0,ratio:0};
    if(points.length<2||!start||!end){result.details.push('Plot a route from the green start to the red end.');return result;}
    const first=points[0],last=points[points.length-1];
    if(distance(first,coord(end))<=cfg.endpointTolerance&&distance(last,coord(start))<=cfg.endpointTolerance){result.details.push('Route planned in reverse: 0 marks.');result.violations.push({points,label:'Route reversed'});return result;}
    const references=[{edges:q.optimalEdges,length:q.optimalLength},...(q.acceptable||[]).filter(a=>a.edges)];
    const referenceClosed=new Set((q.closedEdges||[]).map(String));
    for(const reference of references){if(!reference.edges)continue;const es=reference.edges.map(id=>g.edges.get(String(id))).filter(Boolean);if(!es.length||es.length!==reference.edges.length||es[0].from!==String(q.start)||es[es.length-1].to!==String(q.end)||es.some((e,i)=>referenceClosed.has(e.id)||(i>0&&(es[i-1].to!==e.from||g.banned.has(es[i-1].id+'|'+e.id)))))continue;if(followsReference(points,geometry(es),cfg.referenceTolerance)){
      result.score=total;result.correct=true;result.length=reference.length;result.ratio=reference.length/q.optimalLength;result.matched=reference.edges.slice();result.streets=streetList(es);result.details.push('The drawing follows a verified legal reference route within '+cfg.referenceTolerance+' m screen-matching tolerance.');return result;
    }}
    let deduction=0;
    function loss(n,label,pts){deduction+=n;result.details.push(label+' (−'+n+')');if(pts)result.violations.push({points:pts,label});}
    if(distance(first,coord(start))>cfg.endpointTolerance)loss(cfg.endpointDeduction,'Start is more than '+cfg.endpointTolerance+' m from its marker',[first]);
    if(distance(last,coord(end))>cfg.endpointTolerance)loss(cfg.endpointDeduction,'End is more than '+cfg.endpointTolerance+' m from its marker',[last]);
    let prior=null;const closed=new Set((q.closedEdges||[]).map(String)),violated=new Set();
    for(let i=1;i<points.length;i++){
      const a=points[i-1],b=points[i];if(distance(a,b)<1)continue;const na=nearest(a),nb=nearest(b);
      const matched=na.node&&nb.node&&na.distance<=cfg.corridor+15&&nb.distance<=cfg.corridor+15?path(na.node.id,nb.node.id,{physical:true,allow:e=>e.geometry.every(p=>segmentDistance(p,a,b)<=cfg.corridor)}):null;
      if(!matched || (!matched.length&&distance(a,b)>cfg.corridor*2)){loss(cfg.offroadDeduction,'Segment '+i+' leaves the road network',[a,b]);result.length+=distance(a,b);prior=null;continue;}
      for(const e of matched){
        if(prior&&prior.id===e.id)continue;
        const original=e.originalId||e.parentId||e.id;
        const key=e.wrongWay?'wrong:'+(e.osmWay||original):closed.has(original)?'closed:'+(e.name||original):null;
        if(key&&!violated.has(key)){loss(cfg.illegalDeduction,e.wrongWay?'Wrong way on '+e.name:'Closed road: '+e.name,e.geometry);violated.add(key);}
        if(prior&&g.banned.has((prior.originalId||prior.parentId||prior.id)+'|'+original)){const turn='turn:'+(prior.parentId||prior.id)+'|'+original;if(!violated.has(turn)){loss(cfg.illegalDeduction,'Prohibited turn into '+e.name,e.geometry);violated.add(turn);}}
        result.length+=e.length;if(result.matched[result.matched.length-1]!==original)result.matched.push(original);prior=e;
      }
    }
    result.ratio=result.length/(q.optimalLength||1);
    const alt=(q.acceptable||[]).some(a=>{const ids=Array.isArray(a)?a:a.edges;return ids&&ids.map(String).join('|')===result.matched.join('|');});
    if(!alt){const band=cfg.directness.find(pair=>result.ratio<=pair[0]);if(band&&band[1])loss(band[1],'Route is '+Math.round((result.ratio-1)*100)+'% longer than the shortest legal route');}
    result.score=Math.max(0,total-deduction);result.correct=result.score===total;result.streets=streetList(result.matched.map(id=>g.edges.get(id)||{name:'Wrong-way segment'}));
    if(!deduction)result.details.push('Correct endpoints, legal route and within the directness allowance.');return result;
  }
  window.PHV_Routing={graph,distance,nearest,path,geometry,optimalPoints,optimalEdges,streetList,grade,coord};
}());
