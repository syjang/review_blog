#!/usr/bin/env python3
"""
배치 리뷰 생성 스크립트
 - main_with_search.create_workflow 를 사용해 비대화식으로 여러 제품 리뷰를 생성
 - 사용법:
   python3 auto/batch_generate.py --file auto/product_seeds.txt
   또는
   python3 auto/batch_generate.py --items "아이폰 16 프로 맥스, 갤럭시 S25 울트라, 아이패드 프로 M4"
"""

import argparse
import time
from datetime import datetime
from typing import List

from main_with_search import create_workflow
import json
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, help="제품명 목록 파일(줄바꿈 구분)")
    parser.add_argument(
        "--items", type=str, help="쉼표로 구분된 제품명 목록", default=""
    )
    parser.add_argument(
        "--from-reviews",
        action="store_true",
        help="generated_reviews.json에서 product_name 사용",
    )
    parser.add_argument(
        "--recursion-limit", type=int, default=40, help="LangGraph recursion limit"
    )
    return parser.parse_args()


def load_items_from_file(path: str) -> List[str]:
    items: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name:
                    items.append(name)
    except Exception as e:
        print(f"❌ 목록 파일 읽기 실패: {e}")
    return items


def main():
    args = parse_args()
    items: List[str] = []

    if args.from_reviews:
        # 루트/auto/generated_reviews.json 또는 루트/generated_reviews.json 탐색
        roots = [os.getcwd(), os.path.dirname(__file__)]
        jr = None
        for r in roots:
            cand = os.path.join(r, "generated_reviews.json")
            if os.path.exists(cand):
                jr = cand
                break
        if jr:
            with open(jr, "r", encoding="utf-8") as f:
                data = json.load(f)
            items.extend(
                [
                    row.get("product_name", "").strip()
                    for row in data
                    if row.get("product_name")
                ]
            )
        else:
            print("⚠️ generated_reviews.json을 찾지 못했습니다.")

    if args.file:
        items.extend(load_items_from_file(args.file))
    if args.items:
        items.extend([x.strip() for x in args.items.split(",") if x.strip()])

    # 기본값 (예시)
    if not items:
        items = [
            "아이폰 16 프로 맥스",
            "갤럭시 S25 울트라",
            "갤럭시 Z 폴드7",
        ]

    print(f"🚀 배치 생성 시작: {len(items)}건")
    app = create_workflow()
    summary = []

    for idx, product in enumerate(items, start=1):
        initial_state = {
            "task": f"{product} 리뷰 작성",
            "product_name": "",
            "search_results": {},
            "posts": [],
            "current_post": {},
            "feedback": "",
            "completed": False,
            "images": [],
        }
        config = {
            "configurable": {
                "thread_id": f"batch_{product}_{datetime.now().timestamp()}"
            }
        }
        print("=" * 60)
        print(f"[{idx}/{len(items)}] {product}")
        for output in app.stream(
            initial_state, {**config, "recursion_limit": args.recursion_limit}
        ):
            for key in output.keys():
                print(f"✅ {key} 완료")
        state = app.get_state(config).values
        filename = state.get("current_post", {}).get("filename", "")
        print(f"📄 생성 파일: {filename}")
        summary.append({"product": product, "filename": filename})
        time.sleep(1.0)  # rate limit 여유

    # 결과 요약 출력
    print("=" * 60)
    print("✨ 배치 생성 완료")
    for s in summary:
        print(f"- {s['product']} -> {s['filename']}")


if __name__ == "__main__":
    main()
