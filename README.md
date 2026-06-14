# ai_remove_flags

이미지 메타데이터 제거와 미세 변형을 일괄 적용합니다.

## 설치

```bash
cd ai_remove_flags
.venv/bin/pip install -r requirements.txt
```

구글드라이브 동기화 추가:

```bash
.venv/bin/pip install google-auth google-auth-oauthlib google-api-python-client
```

## 사용법

### 이미지 처리

```bash
# 기본 (images 폴더에서 output 폴더로)
.venv/bin/python ai_remove_flags.py

# 폴더 지정
.venv/bin/python ai_remove_flags.py /path/to/input -o /path/to/output

# 설정 초기화
.venv/bin/python ai_remove_flags.py --init-config
```

### 구글드라이브 동기화

```bash
# 전체 (다운로드 → 처리 → 업로드)
.venv/bin/python gdrive_sync.py --full

# 다운로드만
.venv/bin/python gdrive_sync.py --download

# 처리만
.venv/bin/python gdrive_sync.py --run-ai

# 업로드만
.venv/bin/python gdrive_sync.py --upload
```

처음 실행 시 브라우저에서 구글 권한 인가를 받습니다.

## 설정

`ai_remove_flags_config.json`에서 설정을 조정할 수 있습니다.

```json
{
  "remove_exif": true,
  "format_convert": "jpeg",
  "brightness_change": 0.02,
  "contrast_change": 0.02,
  "saturation_change": 0.02,
  "add_noise": true,
  "noise_level": 15,
  "resize": true,
  "resize_factor": 0.98,
  "output_dir": "output",
  "verbose": false
}
```

## 기능

- EXIF 메타데이터 제거
- 밝기, 대비, 채도 미세 조정
- 노이즈 추가
- 리사이즈
- 형식 변환 (JPEG, PNG, WebP)
