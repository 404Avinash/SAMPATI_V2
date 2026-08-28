#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI Post-Reboot Verification Script
# Verifies that all required services recover automatically after a reboot.
#
# Checks performed:
#   1. Docker daemon is running
#   2. 'sampati' container is up and in "running" state
#   3. nginx service is active
#   4. /health endpoint returns HTTP 200 (tested via nginx on localhost:80)
#
# Usage:
#   chmod +x deploy/verify_reboot.sh
#   ./deploy/verify_reboot.sh
# ─────────────────────────────────────────────────────────────────────────────

set -uo pipefail

FAILED=0
PASSED=0

echo "========================================================"
echo "   SAMPATI V2 Post-Reboot Verification Suite"
echo "========================================================"
echo ""

# ── 1. Check Docker daemon ───────────────────────────────────────────────────
printf "Checking Docker daemon status ... "
if systemctl is-active --quiet docker 2>/dev/null || docker info >/dev/null 2>&1; then
    echo "[PASS]"
    echo "  -> Docker daemon is active and responding."
    PASSED=$((PASSED + 1))
else
    echo "[FAIL]"
    echo "  -> Docker daemon is not active or not responding."
    FAILED=$((FAILED + 1))
fi

# ── 2. Check 'sampati' container state ──────────────────────────────────────
printf "Checking 'sampati' container state ... "
CONTAINER_STATUS=$(docker inspect -f '{{.State.Status}}' sampati 2>/dev/null || true)
CONTAINER_STATUS="${CONTAINER_STATUS:-not_found}"
CONTAINER_RUNNING=$(docker inspect -f '{{.State.Running}}' sampati 2>/dev/null || true)
CONTAINER_RUNNING="${CONTAINER_RUNNING:-false}"

if [ "$CONTAINER_RUNNING" = "true" ]; then
    echo "[PASS]"
    echo "  -> Container 'sampati' is in running state (Status: $CONTAINER_STATUS)."
    PASSED=$((PASSED + 1))
else
    echo "[FAIL]"
    echo "  -> Container 'sampati' is not running (Status: $CONTAINER_STATUS)."
    FAILED=$((FAILED + 1))
fi

# ── 3. Check nginx service ───────────────────────────────────────────────────
printf "Checking nginx service status ... "
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "[PASS]"
    echo "  -> nginx service is active and running."
    PASSED=$((PASSED + 1))
else
    echo "[FAIL]"
    echo "  -> nginx service is not active."
    FAILED=$((FAILED + 1))
fi

# ── 4. Check /health endpoint via nginx reverse proxy ────────────────────────
printf "Checking /health endpoint via nginx reverse proxy ... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1/health 2>/dev/null || true)
HTTP_CODE="${HTTP_CODE:-000}"

if [ "$HTTP_CODE" = "200" ]; then
    echo "[PASS]"
    HEALTH_BODY=$(curl -s --max-time 5 http://127.0.0.1/health 2>/dev/null || true)
    echo "  -> HTTP 200 OK received from http://127.0.0.1/health."
    if [ -n "$HEALTH_BODY" ]; then
        echo "     Payload: $HEALTH_BODY"
    fi
    PASSED=$((PASSED + 1))
else
    echo "[FAIL]"
    echo "  -> Expected HTTP 200, received HTTP $HTTP_CODE from http://127.0.0.1/health."
    # Fallback debug: check backend port directly
    DIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8000/health 2>/dev/null || true)
    DIRECT_CODE="${DIRECT_CODE:-000}"
    echo "     Direct container check on :8000 returned HTTP $DIRECT_CODE."
    FAILED=$((FAILED + 1))
fi

# ── Optional: Check systemd timer status ─────────────────────────────────────
printf "Checking nightly restart timer status ... "
if systemctl is-active --quiet sampati-nightly-restart.timer 2>/dev/null; then
    echo "[PASS]"
    echo "  -> sampati-nightly-restart.timer is active and armed."
else
    echo "[WARN]"
    echo "  -> sampati-nightly-restart.timer is inactive or not installed."
fi

echo ""
echo "========================================================"
echo "Verification Summary: $PASSED passed, $FAILED failed"
echo "========================================================"

if [ "$FAILED" -eq 0 ]; then
    echo "Result: ALL REBOOT SURVIVAL CHECKS PASSED [OK]"
    exit 0
else
    echo "Result: SOME CHECKS FAILED [ERROR]"
    exit 1
fi
