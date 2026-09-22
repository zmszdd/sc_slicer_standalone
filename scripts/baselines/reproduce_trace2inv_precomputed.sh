#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${TRACE2INV_IMAGE:-zhiychen597/trace2inv-artifact-fse2024:latest}"
OUTPUT_DIR="${ROOT_DIR}/baselines/trace2inv/output/precomputed"

mkdir -p "${OUTPUT_DIR}"

docker run --rm \
    -v "${OUTPUT_DIR}:/output" \
    "${IMAGE}" \
    sh -lc '
        set -eu
        cp RQ1RQ3Results/expected/*.txt RQ1RQ3Results/
        mkdir -p /output/raw
        cp RQ1RQ3Results/expected/AccessControl.txt /output/raw/
        cp RQ1RQ3Results/expected/TimeLocks.txt /output/raw/
        cp RQ1RQ3Results/expected/GasControl.txt /output/raw/
        cp RQ1RQ3Results/expected/ReEntrancy.txt /output/raw/
        cp RQ1RQ3Results/expected/Oracle.txt /output/raw/
        cp RQ1RQ3Results/expected/SpecialStorage.txt /output/raw/
        cp RQ1RQ3Results/expected/DataFlow.txt /output/raw/
        cp RQ1RQ3Results/expected/MoneyFlow.txt /output/raw/
        cp RQ1RQ3Results/RQ1RQ3-Expected.txt /output/
        cp RQ2Study/RQ2-Expected.txt /output/
        cp RQ4Results/RQ4-Expected.txt /output/
        python3.10 RQ1RQ3Results/parse.py > /output/RQ1RQ3-Results-from-packaged-logs.txt
        python3.10 RQ2Study/parseTPFP.py > /output/RQ2-Results.txt
        python3.10 RQ4Results/readGas.py > /output/RQ4-Results.txt
    '

echo "Trace2Inv packaged-result parsing completed"
echo "Output directory: ${OUTPUT_DIR}"
echo "Note: RQ1/RQ3 packaged logs have a small mismatch with the expected summary; see baselines/trace2inv/result-summary.json"
