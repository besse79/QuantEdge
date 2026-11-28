"""Daily research report. No order execution or database mutations."""
import argparse
import json
from datetime import date
from .api import ScanRequest, daily_scan, paper_account
from .daily_plan import build_plan

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--start",type=date.fromisoformat,required=True)
    parser.add_argument("--end",type=date.fromisoformat,required=True)
    parser.add_argument("--market",action="append",required=True)
    parser.add_argument("--provider",default="yahoo")
    args=parser.parse_args()
    reports={}
    for market in sorted(set(args.market)):
        reports[market]=daily_scan(ScanRequest(provider=args.provider,mic=market,start=args.start,end=args.end))
    plan=build_plan(reports,paper_account())
    print(json.dumps({"session":str(args.end),"markets":reports,"plan":plan,"execution_authorized":False},default=str,allow_nan=False))

if __name__=="__main__":
    main()
