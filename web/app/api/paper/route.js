export async function GET(){
 try{const r=await fetch((process.env.QUANTEDGE_API_URL||"http://127.0.0.1:8000")+"/paper",{cache:"no-store",signal:AbortSignal.timeout(20000)});return new Response(await r.text(),{status:r.status,headers:{"Content-Type":"application/json"}});}catch{return Response.json({detail:"Portefeuille indisponible"},{status:503});}
}