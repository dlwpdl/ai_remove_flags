#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

clear
echo "AI Remove Flags"
echo "이미지를 images 폴더에 넣고 실행하면 images/output 폴더에 결과가 저장됩니다."
echo

./run.sh "$@"
STATUS=$?

echo
if [ "$STATUS" -eq 0 ]; then
  echo "완료되었습니다."
else
  echo "오류가 발생했습니다. 위 메시지를 확인하세요."
fi

echo "Enter 키를 누르면 창을 닫습니다."
read -r
exit "$STATUS"
