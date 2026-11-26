#!/bin/bash
# Start the Simulator build on an iPhone simulator, take screenshots and collect logs.
# Usage: ios/simulator_smoke.sh path/to/stringwise.app output-folder
set -euo pipefail

APP="$1"
OUT="$2"
BUNDLE="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP/Info.plist")"
mkdir -p "$OUT"

# Newest available iPhone simulator.
UDID="$(xcrun simctl list devices available -j | python3 -c '
import json, re, sys
data = json.load(sys.stdin)["devices"]
def version(runtime):
    return [int(x) for x in re.findall(r"\d+", runtime.split("iOS")[-1])]
for runtime in sorted((r for r in data if "iOS" in r), key=version, reverse=True):
    phones = [d for d in data[runtime] if d["name"].startswith("iPhone")]
    if phones:
        print(phones[0]["udid"]); break
')"
echo "Simulator: $UDID"
xcrun simctl boot "$UDID" || true
xcrun simctl bootstatus "$UDID" -b

xcrun simctl install "$UDID" "$APP"
# Answer the microphone question in advance; CI has no one to tap Allow.
xcrun simctl privacy "$UDID" grant microphone "$BUNDLE" || true

LAUNCH="$(xcrun simctl launch "$UDID" "$BUNDLE")"
echo "$LAUNCH"
PID="${LAUNCH##*: }"

status=0
for seconds in 6 20 45; do
    sleep $(( seconds - ${last:-0} )); last=$seconds
    xcrun simctl io "$UDID" screenshot "$OUT/after-${seconds}s.png" || true
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "The app stopped within ${seconds} seconds." | tee "$OUT/CRASHED.txt"
        status=1
        break
    fi
done

xcrun simctl spawn "$UDID" log show --last 3m --style compact \
    --predicate "process == \"stringwise\"" > "$OUT/system-log.txt" 2>&1 || true
DATA="$(xcrun simctl get_app_container "$UDID" "$BUNDLE" data 2>/dev/null || true)"
if [ -n "$DATA" ]; then
    find "$DATA" -name '*.txt' -path '*logs*' -exec cp {} "$OUT/" \; 2>/dev/null || true
fi
find ~/Library/Logs/DiagnosticReports -iname 'stringwise*' -exec cp {} "$OUT/" \; 2>/dev/null || true

xcrun simctl shutdown "$UDID" || true
exit $status
