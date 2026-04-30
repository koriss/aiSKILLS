#!/usr/bin/env python3
from pathlib import Path
import argparse, json, datetime
ap=argparse.ArgumentParser(); ap.add_argument('--run-dir', required=False); ap.add_argument('--event-id', required=False); ap.add_argument('--event-json', required=False)
args=ap.parse_args()
now=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
event={}
if args.event_json and Path(args.event_json).exists(): event=json.loads(Path(args.event_json).read_text(encoding='utf-8'))
print(json.dumps({'provider':'telegram','event_id':args.event_id or event.get('event_id'),'status':'sent','stub_delivery':True,'real_external_delivery':False,'acked_at':now}, ensure_ascii=False))
