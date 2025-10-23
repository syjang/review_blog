#!/usr/bin/env python3
"""
품질 미달(구린) 포스트 후보 식별 스크립트
 - 기준: 외부 이미지 핫링크 포함, 자동생성 고지 문구 포함, 섹션 부족/짧은 분량
 - 결과를 auto/to_delete.txt 로 기록
"""

import os
import re
from typing import List

ROOT = os.path.dirname(os.path.dirname(__file__))
POSTS_DIR = os.path.join(ROOT, "app", "posts")
OUTPUT_FILE = "to_delete.txt"


def is_low_quality(content: str) -> List[str]:
    reasons: List[str] = []
    # 외부 이미지 핫링크
    if re.search(r"!\[[^\]]*\]\((https?://)", content):
        reasons.append("external_image")
    # 자동생성 고지 문구
    if "웹 검색 결과를 바탕으로 작성" in content:
        reasons.append("auto_disclaimer")
    # 섹션 수/길이 부족
    if len(content) < 800:
        reasons.append("short_length")
    if content.count("### ") < 4:
        reasons.append("few_sections")
    return reasons


def main():
    targets: List[str] = []
    for name in os.listdir(POSTS_DIR):
        if not (name.endswith(".md") or name.endswith(".mdx")):
            continue
        path = os.path.join(POSTS_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            reasons = is_low_quality(content)
            if reasons:
                targets.append(f"{name}\t{','.join(reasons)}")
        except Exception as e:
            print(f"⚠️ 읽기 실패: {name} - {e}")

    out_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        for line in targets:
            f.write(line + "\n")
    print(f"🧹 삭제 후보 {len(targets)}건 기록: {out_path}")


if __name__ == "__main__":
    main()
