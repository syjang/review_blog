#!/usr/bin/env python3
"""
기존 이미지들을 WebP 형식으로 변환하는 스크립트
"""

import os
import re
from PIL import Image

def convert_images_to_webp():
    """기존 이미지들을 WebP로 변환"""

    image_dir = "../app/public/images"

    if not os.path.exists(image_dir):
        print(f"❌ 이미지 디렉토리가 존재하지 않습니다: {image_dir}")
        return

    # 지원하는 이미지 확장자
    supported_extensions = ('.jpg', '.jpeg', '.png', '.gif')

    converted_count = 0
    total_original_size = 0
    total_webp_size = 0

    print("🖼️ 이미지 WebP 변환 시작...")
    print("="*60)

    # 이미지 파일들 찾기
    for filename in os.listdir(image_dir):
        if not filename.lower().endswith(supported_extensions):
            continue

        original_path = os.path.join(image_dir, filename)

        # 파일명에서 확장자 제거하고 .webp 추가
        base_name = os.path.splitext(filename)[0]
        webp_filename = f"{base_name}.webp"
        webp_path = os.path.join(image_dir, webp_filename)

        # 이미 WebP 파일이 존재하면 건너뛰기
        if os.path.exists(webp_path):
            print(f"⏭️ 이미 존재함: {webp_filename}")
            continue

        try:
            # 원본 파일 크기
            original_size = os.path.getsize(original_path)

            # 이미지 열기
            with Image.open(original_path) as img:
                # RGBA 모드가 아니면 RGB로 변환
                if img.mode in ('RGBA', 'LA'):
                    # 투명도가 있는 이미지는 그대로 유지
                    pass
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # WebP로 저장 (품질 85, 최적화 활성화)
                img.save(webp_path, 'WEBP', quality=85, optimize=True)

            # WebP 파일 크기
            webp_size = os.path.getsize(webp_path)

            # 크기 비교
            reduction_percent = ((original_size - webp_size) / original_size) * 100

            print(f"✅ {filename} → {webp_filename}")
            print(f"   크기: {original_size:,}B → {webp_size:,}B ({reduction_percent:.1f}% 감소)")

            converted_count += 1
            total_original_size += original_size
            total_webp_size += webp_size

        except Exception as e:
            print(f"❌ 변환 실패: {filename} - {e}")

    print("="*60)
    print(f"✨ 변환 완료!")
    print(f"📊 변환된 파일: {converted_count}개")

    if total_original_size > 0:
        total_reduction = ((total_original_size - total_webp_size) / total_original_size) * 100
        print(f"💾 총 크기 절약: {total_original_size - total_webp_size:,}B ({total_reduction:.1f}% 감소)")
        print(f"📈 원본 총 크기: {total_original_size:,}B")
        print(f"📉 WebP 총 크기: {total_webp_size:,}B")

def update_markdown_files():
    """마크다운 파일들의 이미지 경로를 WebP로 업데이트"""

    posts_dir = "../app/posts"

    if not os.path.exists(posts_dir):
        print(f"❌ 포스트 디렉토리가 존재하지 않습니다: {posts_dir}")
        return

    updated_files = 0

    print("\n📝 마크다운 파일 업데이트 시작...")
    print("="*60)

    for filename in os.listdir(posts_dir):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(posts_dir, filename)

        try:
            # 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # 이미지 경로 패턴 찾기 및 교체
            # ![alt](/images/filename.jpg) → ![alt](/images/filename.webp)
            patterns = [
                (r'(/images/[^)]+)\.jpg', r'\1.webp'),
                (r'(/images/[^)]+)\.jpeg', r'\1.webp'),
                (r'(/images/[^)]+)\.png', r'\1.webp'),
                (r'(/images/[^)]+)\.gif', r'\1.webp'),
            ]

            changes_made = False
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    changes_made = True

            # 변경사항이 있으면 파일 저장
            if changes_made:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 업데이트됨: {filename}")
                updated_files += 1
            else:
                print(f"⏭️ 변경사항 없음: {filename}")

        except Exception as e:
            print(f"❌ 업데이트 실패: {filename} - {e}")

    print("="*60)
    print(f"✨ 마크다운 파일 업데이트 완료!")
    print(f"📊 업데이트된 파일: {updated_files}개")

if __name__ == "__main__":
    print("🚀 이미지 WebP 변환 및 경로 업데이트")
    print("="*60)

    # 1. 이미지들을 WebP로 변환
    convert_images_to_webp()

    # 2. 마크다운 파일들의 경로 업데이트
    update_markdown_files()

    print("\n🎉 모든 작업 완료!")