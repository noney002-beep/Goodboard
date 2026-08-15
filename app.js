// Shared chart helpers extracted from menu.html / safety.html
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fmtNum(v){ if(!isFinite(v)||v===0) return '0'; if(v>=1000000) return (v/1000000).toFixed(1)+'M'; if(v>=1000) return (v/1000).toFixed(1)+'k'; if(v<1&&v>0) return v.toFixed(2); return Math.round(v); }
function groupByMonth(recs){
  var map=new Map();
  recs.forEach(function(r){
    var d=(r.record_date||'').slice(0,7);
    if(!d) return;
    if(!map.has(d)) map.set(d,{a:[],t:[]});
    var g=map.get(d);
    var av=parseFloat(r.actual), tv=parseFloat(r.target);
    if(!isNaN(av)) g.a.push(av);
    if(!isNaN(tv)) g.t.push(tv);
  });
  var MS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return [...map.entries()].sort(function(a,b){return a[0].localeCompare(b[0]);}).map(function(e){
    var k=e[0], v=e[1], p=k.split('-');
    return { label: (MS[parseInt(p[1],10)-1]||'?') + ' ' + p[0].slice(2), actual: v.a.length?v.a[v.a.length-1]:0, target: v.t.length?v.t[0]:null };
  });
}
function setLoading(id){ var el=document.getElementById(id); if(el) el.innerHTML='<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-size="8" fill="#b3bac6">loading…</text>'; }
function renderEmpty(id){ var el=document.getElementById(id); if(el) el.innerHTML='<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-size="8" fill="#b3bac6">No data</text>'; }
function setCardSummary(svgId, text){ var summaryId = 'summary_' + svgId; var el = document.getElementById(summaryId); if(!el) return; el.innerHTML = text ? text : '<span>No data</span>'; }
function getSummaryText(records){ if(!records || !records.length) return '<span>No data</span>'; var data = groupByMonth(records); if(!data.length) return '<span>No data</span>'; var last = data[data.length-1]; var actual = isFinite(last.actual) ? fmtNum(last.actual) : '0'; var target = (last.target !== null && isFinite(last.target)) ? fmtNum(last.target) : null; if(target !== null) { return '<span>' + esc(last.label) + '</span>Actual: ' + actual + ' | Target: ' + target; } return '<span>' + esc(last.label) + '</span>Actual: ' + actual; }
function drawChart(svgId, records, color){
  var svg = document.getElementById(svgId); if(!svg) return; var data = groupByMonth(records); if(!data.length){ renderEmpty(svgId); return; }
  var box = svg.getBoundingClientRect(); var W = Math.max(box.width,120)||240; var H = Math.max(box.height,40)||96;
  var pL=22,pR=4,pT=6,pB=22; var cW=W-pL-pR, cH=H-pT-pB;
  var targetLine=null; for(var i=0;i<data.length;i++){ if(data[i].target!==null&&!isNaN(data[i].target)){ targetLine=data[i].target; break; } }
  var vals=data.map(function(d){return d.actual;}); if(targetLine!==null) vals.push(targetLine);
  var maxVal=Math.max.apply(null,vals.filter(function(v){return !isNaN(v)&&v>0}))||1; maxVal*=1.18;
  var n=data.length; var slotW=cW/Math.max(n,1); var bW=Math.max(2,slotW*0.6);
  var parts=[];
  for(var g=1;g<=3;g++){ var gy=pT+cH*(1-g/3); parts.push('<line x1="'+pL+'" y1="'+gy+'" x2="'+(W-pR)+'" y2="'+gy+'" stroke="#e8eaee" stroke-width="0.5"/>'); parts.push('<text x="'+(pL-2)+'" y="'+(gy+3)+'" text-anchor="end" font-size="6.5" fill="#9aa3b2">'+fmtNum(maxVal*g/3)+'</text>'); }
  data.forEach(function(d,i){ var cx=pL+i*slotW+slotW/2; var aV=isNaN(d.actual)?0:d.actual; var bh=aV<=0?0.5:(aV/maxVal)*cH; var by=pT+cH-bh; var fill=(targetLine===null||aV>=targetLine)?color:'#d6605a'; parts.push('<rect x="'+(cx-bW/2)+'" y="'+by+'" width="'+bW+'" height="'+bh+'" rx="1" fill="'+fill+'" opacity="0.88"/>'); if(aV>0) parts.push('<text x="'+cx+'" y="'+(by-1.5)+'" text-anchor="middle" font-size="6.5" fill="'+fill+'" font-weight="700">'+fmtNum(aV)+'</text>'); parts.push('<text x="'+cx+'" y="'+(H-pB+11)+'" text-anchor="middle" font-size="6" fill="#9aa3b2" transform="rotate(-28,'+cx+','+(H-pB+11)+')">'+esc(d.label)+'</text>'); });
  if(targetLine!==null&&targetLine>0){ var ty=pT+cH-(targetLine/maxVal)*cH; parts.push('<line x1="'+pL+'" y1="'+ty+'" x2="'+(W-pR)+'" y2="'+ty+'" stroke="#d6605a" stroke-width="1" stroke-dasharray="4,2" opacity="0.7"/>'); }
  parts.push('<line x1="'+pL+'" y1="'+(pT+cH)+'" x2="'+(W-pR)+'" y2="'+(pT+cH)+'" stroke="#cfd6e0" stroke-width="1"/>'); parts.push('<line x1="'+pL+'" y1="'+pT+'" x2="'+pL+'" y2="'+(pT+cH)+'" stroke="#cfd6e0" stroke-width="1"/>');
  svg.setAttribute('viewBox','0 0 '+W+' '+H); svg.setAttribute('width',W); svg.setAttribute('height',H); svg.innerHTML = parts.join('');
}
function normalizeSearchText(value){ return String(value||'').toLowerCase().replace(/[\s_\/()\-]+/g,''); }
function byMain(recs,kpi,kw){ const key=normalizeSearchText(kw); return recs.filter(function(r){ return (r.kpi||'').toLowerCase()===kpi && (!kw || normalizeSearchText(r.main_kpi).includes(key)); }); }
function bySub(recs,kpi,kw){ const key=normalizeSearchText(kw); return recs.filter(function(r){ return (r.kpi||'').toLowerCase()===kpi && (!kw || normalizeSearchText(r.sub_kpi||r.Sub_KPI).includes(key)); }); }
function byProc(recs,kpi,kw){ const key=normalizeSearchText(kw); return recs.filter(function(r){ return (r.kpi||'').toLowerCase()===kpi && (!kw || normalizeSearchText(r.process_kpi||r.Process_KPI).includes(key)); }); }
