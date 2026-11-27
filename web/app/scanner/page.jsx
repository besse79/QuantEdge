"use client";
import {useState} from "react";
export default function Scanner(){
 const [report,setReport]=useState(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e){e.preventDefault();setBusy(true);setError("");setReport(null);try{
 const r=await fetch("/api/scan",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.fromEntries(new FormData(e.currentTarget)))});
 const data=await r.json();if(!r.ok)throw Error(typeof data.detail==="string"?data.detail:"Scan refusé");setReport(data);
 }catch(e){setError(e.message)}finally{setBusy(false)}}
 return <main><a href="/">Backtesting</a><h1>Sélection quantitative</h1><p>Recherche uniquement — aucune exécution PAPER autorisée.</p><form onSubmit={submit} style={{display:"grid",gap:12,maxWidth:420}}>
 <label>Marché <select name="mic"><option>XPAR</option><option>XNYS</option><option>XNAS</option><option>XAMS</option><option>XBRU</option><option>XLIS</option></select></label>
 <label>Fournisseur <input name="provider" defaultValue="yahoo" required/></label>
 <label>Début historique <input name="start" type="date" required/></label><label>Séance <input name="end" type="date" required/></label>
 <button disabled={busy}>{busy?"Analyse en cours":"Analyser"}</button></form>{error&&<p role="alert">{error}</p>}
 {report&&<><h2>{report.ranked.length} classés / {report.unique_candidates} instruments</h2><table><thead><tr><th>Instrument</th><th>Devise</th><th>Momentum</th><th>Candidat</th></tr></thead><tbody>{report.ranked.map((r,i)=><tr key={i}><td>{r.instrument_id}</td><td>{r.currency}</td><td>{(100*r.momentum).toFixed(2)} %</td><td>{r.research_candidate?"Oui":"Non"}</td></tr>)}</tbody></table><h2>Exclusions ({report.rejected.length})</h2><details><summary>Afficher les motifs</summary><ul>{report.rejected.map((r,i)=><li key={i}>{r.instrument_id} : {r.reason}</li>)}</ul></details></>}</main>
}