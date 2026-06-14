#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"
REQ_STAMP="$VENV_DIR/.requirements.stamp"

mkdir -p images/output

if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] 로컬 가상환경을 생성합니다: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

if [ ! -f "$REQ_STAMP" ] || [ requirements.txt -nt "$REQ_STAMP" ]; then
  echo "[setup] 필요한 패키지를 설치합니다."
  python -m pip install --disable-pip-version-check -r requirements.txt
  touch "$REQ_STAMP"
fi

echo "입력 폴더: $(pwd)/images"
echo "출력 폴더: $(pwd)/images/output"
echo

python ai_remove_flags.py "$@"
