#!/usr/bin/env python3
from pathlib import Path
import argparse
from common_runtime import AXES, SOURCE_FAMILIES, now, jwrite
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--topic", required=True); ap.add_argument("--out-dir", required=True); ap.add_argument("--task-id", default="task"); args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    units=[]
    for i,axis in enumerate(AXES,1):
        collection=axis not in ["synthesis_merge","raw_evidence_vault"]
        units.append({"work_unit_id":f"WU-{i:03d}-{axis.replace('_','-')}","axis":axis,"objective":f"Execute {axis} coverage.","status":"planned","collection_unit":collection,"minimum_queries":3 if collection else 0,"minimum_sources":2 if collection else 0,"search_modes":["broad","exact","negative","primary","freshness","source_specific"] if collection else [],"source_families":SOURCE_FAMILIES,"required_outputs":["sources.json","claims.json","evidence.json","errors.json"] if collection else ["result.json"]})
    jwrite(out/"work-unit-plan.json", {"task_id":args.task_id,"min_work_units":8,"work_units":units,"compiled_at":now(),"status":"planned"})
    jwrite(out/"coverage-matrix.json", {"task_id":args.task_id,"axes":[{"axis_id":f"AX-{i:03d}","axis":axis,"required":True,"reason":f"Universal coverage axis {axis}","status":"planned","work_unit_ids":[units[i-1]["work_unit_id"]]} for i,axis in enumerate(AXES,1)],"minimum_axes_required":8,"complete":False})
    print(out)
if __name__=="__main__":
    main()
