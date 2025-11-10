#!/usr/bin/env python3
"""
삭제 후보 파일 이동 스크립트
 - auto/to_delete.txt 를 읽어 app/posts 내 파일을 안전하게 보관 폴더로 이동(.trash-타임스탬프)
"""

import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "app", "posts")
LIST_FILE = os.path.join(os.path.dirname(__file__), "to_delete.txt")


def main():
    if not os.path.exists(LIST_FILE):
        print(f"❌ 목록 파일이 없습니다: {LIST_FILE}")
        return

    trash_dir = os.path.join(
        POSTS_DIR, f".trash-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    os.makedirs(trash_dir, exist_ok=True)

    moved = 0
    with open(LIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            filename = line.strip().split("\t")[0]
            if not filename:
                continue
            src = os.path.join(POSTS_DIR, filename)
            if not os.path.exists(src):
                print(f"⏭️  없음: {filename}")
                continue
            dst = os.path.join(trash_dir, filename)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print(f"🗑️  이동: {filename} → {os.path.relpath(dst, POSTS_DIR)}")
            moved += 1

    print(f"✅ 이동 완료: {moved}개, 보관 폴더: {trash_dir}")


if __name__ == "__main__":
    main()
