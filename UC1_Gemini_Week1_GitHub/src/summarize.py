"""Reproducible descriptive statistics from raw baseline CSV (no accuracy claims)."""
import csv, json, statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'results/baseline_results.csv'
if not source.exists(): raise SystemExit('Run baseline.py first')
rows=list(csv.DictReader(source.open(encoding='utf-8')))
by=defaultdict(list)
for r in rows: by[r['temperature']].append(r)
summary={'test_set_size':25,'attempted_requests':len(rows),'by_temperature':{}}
for temp,items in by.items():
    ok=[r for r in items if r['status']=='ok']
    lat=[float(r['latency_seconds']) for r in ok if r['latency_seconds']]
    summary['by_temperature'][temp]={'attempted':len(items),'successful':len(ok),
      'latency_p50_s':round(statistics.median(lat),3) if lat else None,
      'input_tokens':sum(int(r['input_tokens']) for r in ok if r['input_tokens']),
      'output_tokens':sum(int(r['output_tokens']) for r in ok if r['output_tokens'])}
out=ROOT/'results/baseline_summary.json'
out.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
