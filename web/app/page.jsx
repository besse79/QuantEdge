"use client";
import {useEffect,useState} from "react";
const pct=n=>Number.isFinite(n)?(100*n).toFixed(2)+" %":"—";
function Curve({values,label}){
 if(!values.length)return null;
 const lo=Math.min(...values),hi=Math.max(...values),span=hi-lo||1;
 const points=values.map((v,i)=>[20+760*i/Math.max(1,values.length-1),180-160*(v-lo)/span].join(",")).join(" ");
 return <figure><figcaption>{label} — {lo.toFixed(2)} à {hi.toFixed(2)}</figcaption><svg viewBox="0 0 800 200" role="img" aria-label={label} style={{width:"100%",border:"1px solid #ddd"}}><polyline points={points} fill="none" stroke="#2563eb" strokeWidth="2"/></svg></figure>;
}
export default function Page(){
 const [catalog,setCatalog]=useState([]),[selected,setSelected]=useState(""),[query,setQuery]=useState(""),[result,setResult]=useState(null),[error,setError]=useState(""),[busy,setBusy]=useState(false),[loading,setLoading]=useState(true);
 useEffect(()=>{fetch("/api/instruments").then(async r=>{if(!r.ok)throw Error("Catalogue indisponible");return r.json()}).then(setCatalog).catch(e=>setError(e.message)).finally(()=>setLoading(false))},[]);
 const instrument=catalog[Number(selected)];const filtered=catalog.map((x,i)=>({x,i})).filter(({x})=>[x.symbol,x.name,x.mic].join(" ").toLowerCase().includes(query.toLowerCase()));
 async function submit(e){e.preventDefault();if(selected===""||!instrument)return;setBusy(true);setError("");setResult(null);
 const data=Object.fromEntries(new FormData(e.currentTarget));Object.assign(data,{instrument_id:instrument.instrument_id,provider:instrument.provider,currency:instrument.currency,cash:Number(data.cash),fee:Number(data.fee)});
 try{const r=await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});const body=await r.json();if(!r.ok)throw Error(typeof body.detail==="string"?body.detail:"Requête refusée");setResult(body);}catch(e){setError(e.message);}finally{setBusy(false);}}
 const values=result?.result.snapshots.map(s=>s.equity)||[];let peak=result?.initial_cash||0;const dd=values.map(v=>{peak=Math.max(peak,v);return peak?100*(1-v/peak):0});
 return <main><a href="/scanner">Sélection quantitative</a><h1>QuantEdge — Recherche</h1><p>Simulation uniquement. Aucun ordre réel.</p><form onSubmit={submit} style={{display:"grid",gap:12,maxWidth:650}}>
 <label>Rechercher une action<input value={query} onChange={e=>{setQuery(e.target.value);setSelected("")}} /></label>
 <label>Instrument<select required value={selected} onChange={e=>setSelected(e.target.value)}><option value="">{loading?"Chargement…":"Sélectionner"}</option>{filtered.map(({x,i})=><option key={i} value={i}>{x.symbol} — {x.name} ({x.mic}, {x.currency}, {x.provider})</option>)}</select></label>
 <label>Calendrier<input name="calendar" key={selected} defaultValue={instrument?.mic||"XPAR"} required/></label>
 {["history_start","start","end","cash","fee"].map(k=><label key={k}>{({history_start:"Début historique",start:"Début simulation",end:"Fin simulation",cash:"Capital",fee:"Frais par ordre"})[k]}<input style={{display:"block",width:"100%"}} name={k} required type={["history_start","start","end"].includes(k)?"date":"number"} step="any" defaultValue={{cash:500,fee:0}[k]}/></label>)}
 <button disabled={busy||selected===""}>{busy?"Calcul en cours":"Lancer le backtest"}</button></form>{error&&<p role="alert">{error}</p>}{result&&<section><h2>Performances</h2><p>Rendement : {pct(result.metrics.total_return)} · Drawdown : {pct(result.metrics.max_drawdown)} · Benchmark : {pct(result.metrics.benchmark?.total_return)} · Sharpe : {result.metrics.sharpe_zero_rf_252?.toFixed(2)??"—"}</p><Curve values={values} label="Capital"/><Curve values={dd} label="Drawdown (%)"/><h2>Transactions</h2><table><thead><tr>{["Date","Sens","Quantité","Prix"].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{result.result.trades.map((t,i)=><tr key={i}><td>{t.day}</td><td>{t.side}</td><td>{t.quantity}</td><td>{t.price}</td></tr>)}</tbody></table></section>}</main>
}