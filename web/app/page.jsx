"use client";
import {useState} from "react";
export default function Page(){
 const [result,setResult]=useState(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e){e.preventDefault();setBusy(true);setError("");setResult(null);
 const data=Object.fromEntries(new FormData(e.currentTarget));data.cash=Number(data.cash);data.fee=Number(data.fee);
 try{const r=await fetch("/api/research",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});const body=await r.json();if(!r.ok)throw Error(typeof body.detail==="string"?body.detail:"Requête refusée");setResult(body);}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <main><h1>QuantEdge — Recherche</h1><p>Simulation uniquement. Aucun ordre réel.</p><form onSubmit={submit} style={{display:"grid",gap:12,maxWidth:550}}>
 {["instrument_id","provider","currency","calendar","history_start","start","end","cash","fee"].map(k=><label key={k}>{k}<input style={{display:"block",width:"100%"}} name={k} required type={["history_start","start","end"].includes(k)?"date":["cash","fee"].includes(k)?"number":"text"} step="any" defaultValue={{cash:500,fee:0,currency:"EUR",calendar:"XPAR",provider:"yahoo"}[k]}/></label>)}
 <button disabled={busy}>{busy?"Calcul en cours":"Lancer le backtest"}</button></form>{error&&<p role="alert">{error}</p>}{result&&<section><h2>Performances</h2><pre>{JSON.stringify(result.metrics,null,2)}</pre><h2>Transactions</h2><table><thead><tr>{["Date","Sens","Quantité","Prix"].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{result.result.trades.map((t,i)=><tr key={i}><td>{t.day}</td><td>{t.side}</td><td>{t.quantity}</td><td>{t.price}</td></tr>)}</tbody></table></section>}</main>
}