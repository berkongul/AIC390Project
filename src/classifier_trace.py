"""Run only the request classifier on the 40 test cases and save every attempt (W2.1 evidence).

Writes results/classifier/<UTC time>/:
  manifest.json   model, git commit, hashes of the classifier prompt, schema and test set
  trace.jsonl     one line per case: expected and returned JSON, field checks, every attempt
                  (outcome, problems, raw output), tokens and model time
  summary.json    exact match and field accuracy with n and 95% intervals, retries, fail-closed
                  cases, cost and latency

Run:  python src/classifier_trace.py              (40 Groq calls plus retries, about 4 minutes)
      python src/classifier_trace.py --limit 3    (first 3 cases, to check the key)
"""
import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_week1 import PRICE_IN, PRICE_OUT  # noqa: E402
from week2 import CLASSIFIER, ROOT, SCHEMA, Model, classify  # noqa: E402
from week2_stats import rate  # noqa: E402

CASES = ROOT / 'tests' / 'week2_cases.json'


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def fields(expected, got):
    got = got or {'intent': None, 'urgency': None, 'entities': {'order_ids': None, 'product_codes': None}}
    return {
        'intent': got['intent'] == expected['intent'],
        'urgency': got['urgency'] == expected['urgency'],
        'order_ids': got['entities']['order_ids'] == expected['entities']['order_ids'],
        'product_codes': got['entities']['product_codes'] == expected['entities']['product_codes'],
    }


def cost(calls):
    p_in = float(os.getenv('GROQ_INPUT_USD_PER_MILLION') or PRICE_IN)
    p_out = float(os.getenv('GROQ_OUTPUT_USD_PER_MILLION') or PRICE_OUT)
    ok = [c for c in calls if c['status'] == 'ok']
    return sum(c['input_tokens'] * p_in + c['output_tokens'] * p_out for c in ok) / 1e6


def summarise(rows, calls, model_name):
    n = len(rows)
    out = {'model': model_name, 'n': n,
           'exact_match': rate(sum(r['exact'] for r in rows), n)}
    for key in ('intent', 'urgency', 'order_ids', 'product_codes'):
        out[f'{key}_accuracy'] = rate(sum(r['fields'][key] for r in rows), n)
    out['valid_first_try'] = rate(sum(r['attempts'][0]['outcome'] == 'ok' for r in rows), n)
    out['valid_after_retries'] = rate(sum(r['returned'] is not None for r in rows), n)
    out['attempts_per_case'] = dict(sorted(Counter(len(r['attempts']) for r in rows).items()))
    out['failed_attempt_outcomes'] = dict(Counter(a['outcome'] for r in rows for a in r['attempts'] if a['outcome'] != 'ok'))
    out['retried_cases'] = [{'id': r['id'], 'outcomes': [a['outcome'] for a in r['attempts']]}
                            for r in rows if len(r['attempts']) > 1]
    out['fail_closed'] = [r['id'] for r in rows if r['returned'] is None]
    out['mismatches'] = [{'id': r['id'], 'wrong': [k for k, ok in r['fields'].items() if not ok]}
                         for r in rows if not r['exact']]
    out['cost_per_message_usd'] = round(cost(calls) / n, 8)
    out['spend_usd'] = round(cost(calls), 6)
    out['latency_p50_s'] = round(statistics.median(r['model_seconds'] for r in rows), 3)
    out['calls'] = {'ok': sum(c['status'] == 'ok' for c in calls),
                    'failed': sum(c['status'] != 'ok' for c in calls)}
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--limit', type=int, help='only the first N cases')
    parser.add_argument('--pause', default='5', help='seconds to wait after each call (rate limits)')
    args = parser.parse_args()
    os.environ['WEEK2_PAUSE_SECONDS'] = args.pause

    cases = json.loads(CASES.read_text(encoding='utf-8'))[:args.limit]
    model = Model()
    output = ROOT / 'results' / 'classifier' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(['git', 'status', '--porcelain', 'src', 'tests'], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    (output / 'manifest.json').write_text(json.dumps({
        'model': model.name, 'temperature': 0, 'git_commit': commit, 'uncommitted_changes': dirty,
        'classifier_prompt_sha256': sha(CLASSIFIER), 'schema_sha256': sha(json.dumps(SCHEMA, sort_keys=True)),
        'test_set_sha256': hashlib.sha256(CASES.read_bytes()).hexdigest(), 'cases': len(cases),
        'pause_seconds': args.pause}, indent=2) + '\n', encoding='utf-8')

    rows = []
    with (output / 'trace.jsonl').open('w', encoding='utf-8') as f:
        for case in cases:
            start = len(model.calls)
            attempts = []
            returned, errors = classify(model, case['input'], trace=attempts)
            calls = model.calls[start:]
            checks = fields(case['expected'], returned)
            row = {'id': case['id'], 'tags': case['tags'], 'input': case['input'],
                   'expected': case['expected'], 'returned': returned, 'fields': checks,
                   'exact': returned == case['expected'], 'attempts': attempts, 'errors': errors,
                   'input_tokens': sum(c['input_tokens'] or 0 for c in calls),
                   'output_tokens': sum(c['output_tokens'] or 0 for c in calls),
                   'model_seconds': round(sum(c['latency_s'] for c in calls if c['status'] == 'ok'), 3)}
            rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
            f.flush()
            print(f"{case['id']} {'ok ' if row['exact'] else 'MISMATCH'} attempts={len(attempts)} "
                  f"{[a['outcome'] for a in attempts] if len(attempts) > 1 else ''}", flush=True)

    summary = summarise(rows, model.calls, model.name)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (output / 'calls.json').write_text(json.dumps(model.calls, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('exact_match', 'valid_first_try', 'attempts_per_case',
                                               'failed_attempt_outcomes', 'fail_closed', 'mismatches',
                                               'cost_per_message_usd', 'latency_p50_s')}, indent=2))
    print(f'Evidence: {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
