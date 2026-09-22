#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE="${INVCON_IMAGE:-liuyedocker/invcon:latest}"
ADDRESS="0x0e9d46eed51a527db8f5c12a803eb7fddf4da332"
CONTRACT="TokenERC20"
CONTAINER_NAME="sc-slicer-invcon-cached-example"
OUTPUT_DIR="${ROOT_DIR}/baselines/invcon/output/official_cached_case"
CACHE_DIR="/home/liuye/Projects/InvCon/Experiment/ERC20/${ADDRESS}"

cleanup() {
    docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}

if docker container inspect "${CONTAINER_NAME}" >/dev/null 2>&1; then
    echo "Container already exists: ${CONTAINER_NAME}" >&2
    echo "Remove it manually after confirming it is disposable." >&2
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"
trap cleanup EXIT

docker run --name "${CONTAINER_NAME}" "${IMAGE}" \
    invcon --eth_address "${ADDRESS}"

docker cp "${CONTAINER_NAME}:${CACHE_DIR}/." "${OUTPUT_DIR}/"

if [[ ! -s "${OUTPUT_DIR}/${CONTRACT}.inv" ]]; then
    echo "InvCon did not produce ${OUTPUT_DIR}/${CONTRACT}.inv" >&2
    exit 1
fi

echo "InvCon reproduction succeeded"
echo "Invariant file: ${OUTPUT_DIR}/${CONTRACT}.inv"
