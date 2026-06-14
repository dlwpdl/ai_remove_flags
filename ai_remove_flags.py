#!/usr/bin/env python3
import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Optional

import cv2  # noqa: F401 - opencv-python 설치 확인용, 추후 OpenCV 처리 확장 대비
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import tqdm


# 이미지 확장자
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff', '.tif'}

# 기본 설정
DEFAULT_CONFIG = {
    "remove_exif": True,
    "format_convert": "jpeg",
    "brightness_change": 0.02,
    "contrast_change": 0.02,
    "saturation_change": 0.02,
    "add_noise": True,
    "noise_level": 15,
    "resize": True,
    "resize_factor": 0.98,
    "output_dir": "output",
    "verbose": False
}


def load_config(config_path: str = 'ai_remove_flags_config.json') -> dict:
    """설정 파일 로드. 없으면 기본값 사용."""
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        config.update(user_config)

    return config


def save_config(config: dict, config_path: str = 'ai_remove_flags_config.json') -> None:
    """설정 파일 저장."""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"설정 파일 저장: {config_path}")


def strip_metadata(image: Image.Image) -> Image.Image:
    """메타데이터 제거."""
    clean_image = image.copy()
    clean_image.info.clear()
    return clean_image


def apply_noise(image: Image.Image, noise_level: float) -> Image.Image:
    """알파 채널은 보존하면서 노이즈 추가."""
    if noise_level <= 0:
        return image

    img_array = np.array(image).astype(np.float32)

    if img_array.ndim == 3 and img_array.shape[2] == 4:
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3:]
        noise = np.random.normal(0, noise_level, rgb.shape)
        rgb = np.clip(rgb + noise, 0, 255)
        img_array = np.concatenate([rgb, alpha], axis=2)
    else:
        noise = np.random.normal(0, noise_level, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)

    return Image.fromarray(img_array.astype(np.uint8), mode=image.mode)


def apply_subtle_changes(image: Image.Image, config: dict) -> Image.Image:
    """미세 변형 적용."""
    img = image.copy()

    if img.mode == 'P':
        img = img.convert('RGBA')
    elif img.mode == '1':
        img = img.convert('L')

    # 밝기
    if abs(config['brightness_change']) > 0:
        factor = random.uniform(
            1 - config['brightness_change'],
            1 + config['brightness_change']
        )
        img = ImageEnhance.Brightness(img).enhance(factor)

    # 대비
    if abs(config['contrast_change']) > 0:
        factor = random.uniform(
            1 - config['contrast_change'],
            1 + config['contrast_change']
        )
        img = ImageEnhance.Contrast(img).enhance(factor)

    # 채도
    if abs(config['saturation_change']) > 0:
        factor = random.uniform(
            1 - config['saturation_change'],
            1 + config['saturation_change']
        )
        img = ImageEnhance.Color(img).enhance(factor)

    # 노이즈 추가
    if config['add_noise']:
        img = apply_noise(img, float(config['noise_level']))

    return img


def resize_image(image: Image.Image, config: dict) -> Image.Image:
    """이미지 크기 변경."""
    if not config['resize']:
        return image

    factor = random.uniform(
        config['resize_factor'] - 0.002,
        config['resize_factor'] + 0.002
    )
    w, h = image.size
    new_size = (max(1, int(round(w * factor))), max(1, int(round(h * factor))))
    return image.resize(new_size, Image.LANCZOS)


def get_output_extension(input_path: str, config: dict) -> str:
    """설정에 맞는 출력 확장자 결정."""
    output_format = str(config['format_convert']).lower()
    input_ext = Path(input_path).suffix.lower()

    if output_format == 'jpeg':
        return '.jpg'
    if output_format == 'png':
        return '.png'
    if output_format == 'webp':
        return '.webp'
    if output_format in ('none', 'original'):
        return input_ext

    raise ValueError(f"지원하지 않는 format_convert 값: {config['format_convert']}")


def convert_for_output(image: Image.Image, output_ext: str) -> Image.Image:
    """저장 형식에 맞게 이미지 모드 변환."""
    if output_ext in ('.jpg', '.jpeg') and image.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        alpha = image.getchannel('A') if image.mode in ('RGBA', 'LA') else None
        background.paste(image.convert('RGB'), mask=alpha)
        return background

    return image


def build_output_path(
    input_path: Path,
    output_dir: Path,
    output_ext: str,
    input_root: Optional[Path] = None
) -> Path:
    """출력 경로 생성. 폴더 처리 시 하위 경로를 유지."""
    if input_root is not None:
        relative_path = input_path.relative_to(input_root).with_suffix(output_ext)
        return output_dir / relative_path

    return output_dir / f"{input_path.stem}{output_ext}"


def save_image(image: Image.Image, output_path: Path, output_ext: str) -> None:
    """확장자에 맞춰 이미지 저장."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_ext in ('.jpg', '.jpeg'):
        image.save(output_path, 'JPEG', quality=95, subsampling=0)
    elif output_ext == '.png':
        image.save(output_path, 'PNG', compress_level=9)
    elif output_ext == '.webp':
        image.save(output_path, 'WEBP', quality=95)
    else:
        image.save(output_path)


def process_image(
    input_path: str,
    config: dict,
    output_dir: str,
    input_root: Optional[str] = None
) -> str:
    """단일 이미지 처리."""
    source_path = Path(input_path)
    root_path = Path(input_root) if input_root else None

    with Image.open(source_path) as opened_image:
        # EXIF orientation은 이미지에 반영한 뒤 메타데이터를 제거한다.
        image = ImageOps.exif_transpose(opened_image)

        if config['remove_exif']:
            image = strip_metadata(image)

        image = apply_subtle_changes(image, config)
        image = resize_image(image, config)

        output_ext = get_output_extension(str(source_path), config)
        image = convert_for_output(image, output_ext)
        output_path = build_output_path(source_path, Path(output_dir), output_ext, root_path)
        save_image(image, output_path, output_ext)

    if config['verbose']:
        print(f"  저장됨: {output_path}")

    return str(output_path)


def is_relative_to(path: Path, base: Path) -> bool:
    """Python 버전 호환용 하위 경로 체크."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def collect_image_files(input_dir: Path, output_dir: Path, recursive: bool) -> list[Path]:
    """이미지 파일 수집. 출력 폴더는 입력에서 제외."""
    candidates = input_dir.rglob('*') if recursive else input_dir.glob('*')
    image_files = []

    for file_path in candidates:
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if is_relative_to(file_path, output_dir):
            continue
        image_files.append(file_path)

    return sorted(image_files)


def process_directory(
    input_dir: str,
    config: dict,
    output_dir: str,
    recursive: bool = True
) -> dict:
    """폴더 전체 처리."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    image_files = collect_image_files(input_path, output_path, recursive)

    if not image_files:
        print("이미지 파일을 찾지 못했습니다.")
        return {'success': 0, 'failed': 0, 'total': 0}

    output_path.mkdir(parents=True, exist_ok=True)

    results = {'success': 0, 'failed': 0, 'total': len(image_files)}

    print(f"\n처리 대상: {len(image_files)}개 파일")
    print(f"출력 폴더: {output_path}")
    print("-" * 60)

    for file_path in tqdm.tqdm(image_files, desc="처리 중"):
        try:
            process_image(str(file_path), config, str(output_path), str(input_path))
            results['success'] += 1
        except Exception as e:
            if config['verbose']:
                print(f"\n오류: {file_path} - {e}")
            results['failed'] += 1

    print("-" * 60)
    print(f"완료! 성공: {results['success']} | 실패: {results['failed']}")
    return results


def resolve_output_dir(input_dir: Path, output_dir: str) -> Path:
    """상대 출력 경로는 입력 폴더 아래로 해석."""
    output_path = Path(output_dir).expanduser()
    if output_path.is_absolute():
        return output_path
    return input_dir / output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="이미지 메타데이터 제거와 미세 변형을 일괄 적용합니다."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="images",
        help="입력 이미지 폴더. 기본값: images"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="ai_remove_flags_config.json",
        help="설정 파일 경로. 기본값: ai_remove_flags_config.json"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="출력 폴더. 상대 경로면 입력 폴더 아래에 생성됩니다."
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="하위 폴더를 재귀 처리하지 않습니다."
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="기본 설정 파일을 생성하고 종료합니다."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그를 출력합니다."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)

    if args.init_config:
        save_config(DEFAULT_CONFIG.copy(), str(config_path))
        return 0

    config = load_config(str(config_path))
    if args.verbose:
        config['verbose'] = True

    input_dir = Path(args.input_dir).expanduser()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"입력 폴더를 찾을 수 없습니다: {input_dir}")
        return 1

    output_dir = resolve_output_dir(input_dir, args.output or config['output_dir'])
    process_directory(
        str(input_dir),
        config,
        str(output_dir),
        recursive=not args.no_recursive
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
