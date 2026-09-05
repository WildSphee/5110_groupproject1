#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${TOUR_DOCX_VENV:-${SCRIPT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install \
    --disable-pip-version-check \
    --quiet \
    --requirement "${SCRIPT_DIR}/requirements.txt"

exec "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/build_tour_de_france_design_report.py"
