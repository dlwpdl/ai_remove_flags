# AI Remove Flags

## 사용법

1. 이미지 파일을 `images/` 폴더에 넣습니다.
2. macOS Finder에서 `run.command`를 더블클릭합니다.
3. 결과 파일은 `images/output/` 폴더에 저장됩니다.

터미널에서 실행할 때는 아래 명령을 사용합니다.

```bash
cd /Users/ash/Desktop/Git/ai_remove_flags
./run.sh
```

## 설정 변경

`ai_remove_flags_config.json`을 편집하면 출력 형식, 밝기/대비/채도 변화량, 노이즈, 리사이즈 여부를 바꿀 수 있습니다.

출력 형식 예시:

```json
"format_convert": "jpeg"
```

사용 가능한 값은 `jpeg`, `png`, `webp`, `none`입니다.
