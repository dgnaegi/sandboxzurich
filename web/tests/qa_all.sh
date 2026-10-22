#!/bin/sh
# Full QA run against the dev server (PC + phone tests). Usage: sh web/tests/qa_all.sh > logs/qaN.log 2>&1
cd "$(dirname "$0")/.."
(npx tsc --noEmit && echo "tsc OK") || echo "tsc FAIL"
for t in gameplay touch drive transit_drive scooter_ride crash knock traffic_legal move_quality qa_spawn qa_leak mem_phone perf; do
  echo "== $t"; node tests/$t.mjs http://localhost:5173 2>&1 | tail -15; echo "rc $?"
done
echo "== bridges_ride"; node tests/bridges_ride.mjs qa 2>&1 | tail -6
echo QA_DONE
