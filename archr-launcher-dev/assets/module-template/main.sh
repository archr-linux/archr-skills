#!/bin/sh
# Oneshot: one JSON-RPC message on stdin, notifications and at most one reply
# on stdout, then exit. Logs go to stderr only.
IFS= read -r msg || exit 0
eval "$(printf '%s' "$msg" | jq -r '@sh "id=\(.id // "null") method=\(.method // "")"')"

seconds=$(jq -r 'if .seconds == true then "true" else "false" end' "$ARCHR_MODULE_SETTINGS" 2>/dev/null)
up=$(cut -d. -f1 /proc/uptime 2>/dev/null)
up=${up:-0}
h=$((up / 3600)); m=$((up % 3600 / 60)); s=$((up % 60))
if [ "$seconds" = true ]; then
    text=$(printf '%d:%02d:%02d' "$h" "$m" "$s")
else
    text=$(printf '%dh %02dmin' "$h" "$m")
fi

for target in tile:uptime row:now; do
    jq -cn --arg t "$target" --arg v "$text" \
        '{jsonrpc:"2.0",method:"ui.update",params:{target:$t,value:$v}}'
done

case "$method" in
    action.invoke) printf '{"jsonrpc":"2.0","id":%s,"result":{}}\n' "$id" ;;
    event) ;;
    *) [ "$id" = null ] || printf '{"jsonrpc":"2.0","id":%s,"error":{"code":-32601,"message":"unknown method"}}\n' "$id" ;;
esac
