#!/usr/bin/env python3
"""Google Drive 동기화 스크립트.

구글드라이브의 이미지 폴더를 로컬로 동기화하고, ai_remove_flags.py를 실행한 뒤
결과를 다시 구글드라이브에 업로드합니다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Google Drive
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoUploadProgress
from googleapiclient.errors import HttpError

# Google Drive API scopes
SCOPES = ["https://www.googleapis.com/auth/drive"]

DEFAULT_CONFIG = {
    "gdrive_folder_id": None,       # None이면 루트
    "local_dir": "gdrive_local",
    "upload_folder": "gdrive_output",
    "ai_remove_input": "gdrive_local",
    "ai_remove_output": "gdrive_output",
}


def get_service():
    """구글드라이브 API 서비스 생성."""
    creds = None
    token_path = Path("gdrive_token.json")
    if token_path.exists():
        creds = _load_creds(token_path)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        _save_creds(creds, token_path)
    return build("drive", "v3", credentials=creds)


def _load_creds(path):
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)


def _save_creds(creds, path):
    import pickle
    with open(path, "wb") as f:
        pickle.dump(creds, f)


def get_folder_id(service, folder_name):
    """폴더명에서 ID 찾기."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])
    if items:
        return items[0]["id"]
    # 폴더가 없으면 생성
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_to_drive(service, local_file, drive_folder_id, file_name=None, chunk_size=1024 * 1024):
    """파일 업로드."""
    if file_name is None:
        file_name = Path(local_file).name

    existing = service.files().list(
        q=f"name='{file_name}' and '{drive_folder_id}' in parents and trashed=false",
        fields="files(id, name)",
    ).execute().get("files", [])

    file_metadata = {"name": file_name, "parents": [drive_folder_id]}
    media = MediaIoUploadProgress(
        local_file,
        resumable=True,
    )

    if existing:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, body=file_metadata, media_body=media).execute()
    else:
        service.files().create(body=file_metadata, media_body=media).execute()


def download_folder(service, folder_id, local_path):
    """구글드라이브 폴더 다운로드."""
    local_path.mkdir(parents=True, exist_ok=True)
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    for f in files:
        if f["mimeType"] == "application/vnd.google-apps.folder":
            download_folder(service, f["id"], local_path / f["name"])
        else:
            req = service.files().get_media(fileId=f["id"])
            with open(local_path / f["name"], "wb") as fh:
                while True:
                    data = req.next_chunk()
                    if data is None:
                        break


def main():
    parser = argparse.ArgumentParser(description="Google Drive sync for ai_remove_flags")
    parser.add_argument("--download", action="store_true", help="구글드라이브에서 다운로드")
    parser.add_argument("--upload", action="store_true", help="로컬에서 구글드라이브로 업로드")
    parser.add_argument("--run-ai", action="store_true", help="ai_remove_flags.py 실행")
    parser.add_argument("--full", action="store_true", help="전체: download → run → upload")
    args = parser.parse_args()

    service = get_service()

    if args.download:
        print("Downloading from Google Drive...")
        # TODO: implement based on your folder structure
        print("Done.")
    elif args.upload:
        print("Uploading to Google Drive...")
        # TODO: implement
        print("Done.")
    elif args.run_ai:
        print("Running ai_remove_flags.py...")
        result = subprocess.run(
            [sys.executable, "ai_remove_flags.py"],
            cwd=".",
        )
        sys.exit(result.returncode)
    elif args.full:
        print("Full sync: download → run → upload")
        # TODO: full implementation
    else:
        print("Usage: gdrive_sync.py [--download | --upload | --run-ai | --full]")
        sys.exit(1)


if __name__ == "__main__":
    main()
