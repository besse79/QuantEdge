"use client";
import {useEffect,useState} from "react";
export default function Paper(){
 const [account,setAccount]=useState(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function refresh(){setBusy(true);setError("");setAccount(null);try{const r=await fetch("/api/paper",{cache:"no-store"});const data=await r.json();if(!r.ok)throw Error(data.detail||"Portefeuille indisponible");setAccount(data)}catch(e){setError(e.message)}finally{setBusy(false)}}
 useEffect(()=>{refresh()},[]);
 return <main><nav><a href="/">Backtesting</a> · <a href="/scanner">Scanner</a></nav><h1>Portefeuille PAPER</h1><p>Consultation uniquement — exécution désactivée.</p><button disabled={busy} onClick={refresh}>Actualiser</button>{error&&<p role="alert">{error}</p>}{account&&<><h2>Liquidités : {Number(account.cash).toFixed(2)} EUR</h2><h2>Positions</h2>{account.positions.length===0?<p>Aucune position</p>:<table><thead><tr><th>Instrument</th><th>Quantité</th></tr></thead><tbody>{account.positions.map(p=><tr key={p.instrument_id}><td>{p.instrument_id}</td><td>{p.quantity}</td></tr>)}</tbody></table>}</>}</main>
}