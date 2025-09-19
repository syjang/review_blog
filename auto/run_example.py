"""
실행 예제
"""

from workflows import run_review_workflow, run_quick_review
from dotenv import load_dotenv
import os
from datetime import datetime

# 환경 변수 로드
load_dotenv()


def save_markdown_file(content: str, product_name: str):
    """마크다운 파일 저장"""
    # 파일명 생성 (공백을 언더스코어로 변경)
    safe_name = product_name.replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.md"

    # outputs 폴더 생성
    os.makedirs("outputs", exist_ok=True)
    filepath = f"outputs/{filename}"

    # 파일 저장
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n📁 파일 저장됨: {filepath}")
    return filepath


def example_full_review():
    """전체 리뷰 워크플로우 예제"""
    print("\n" + "="*60)
    print("🌟 전체 리뷰 워크플로우 예제")
    print("="*60)

    product = "샤오미 미밴드 8"

    # 워크플로우 실행
    result = run_review_workflow(product)

    if result.get("status") == "completed":
        print("\n" + "="*60)
        print("✨ 리뷰 작성 완료!")
        print("="*60)

        # 마크다운 미리보기
        markdown = result.get("markdown", "")
        print("\n📝 마크다운 미리보기:")
        print("-" * 40)
        print(markdown[:500] + "...")

        # 파일 저장
        save_markdown_file(markdown, product)
    else:
        print(f"\n❌ 오류 발생: {result.get('error', '알 수 없는 오류')}")


def example_quick_review():
    """빠른 리뷰 예제"""
    print("\n" + "="*60)
    print("⚡ 빠른 리뷰 워크플로우 예제")
    print("="*60)

    product = "스타벅스 텀블러"
    key_points = [
        "보온 효과 뛰어남",
        "디자인이 깔끔함",
        "가격이 비싼 편",
        "용량이 적당함"
    ]

    # 워크플로우 실행
    result = run_quick_review(product, key_points)

    if result.get("status") == "completed":
        print("\n" + "="*60)
        print("✨ 빠른 리뷰 작성 완료!")
        print("="*60)

        # 마크다운 미리보기
        markdown = result.get("markdown", "")
        print("\n📝 마크다운 미리보기:")
        print("-" * 40)
        print(markdown[:500] + "...")

        # 파일 저장
        save_markdown_file(markdown, product)
    else:
        print("\n❌ 오류 발생")


def interactive_mode():
    """대화형 모드"""
    print("\n" + "="*60)
    print("💬 대화형 리뷰 작성 모드")
    print("="*60)

    while True:
        print("\n옵션을 선택하세요:")
        print("1. 전체 리뷰 작성 (리서치 포함)")
        print("2. 빠른 리뷰 작성")
        print("3. 종료")

        choice = input("\n선택 (1/2/3): ").strip()

        if choice == "1":
            product = input("제품명을 입력하세요: ").strip()
            if product:
                result = run_review_workflow(product)
                if result.get("status") == "completed":
                    save_markdown_file(result.get("markdown", ""), product)

        elif choice == "2":
            product = input("제품명을 입력하세요: ").strip()
            key_points_input = input("주요 포인트를 콤마로 구분해서 입력하세요 (선택사항): ").strip()

            key_points = []
            if key_points_input:
                key_points = [point.strip() for point in key_points_input.split(",")]

            if product:
                result = run_quick_review(product, key_points)
                if result.get("status") == "completed":
                    save_markdown_file(result.get("markdown", ""), product)

        elif choice == "3":
            print("\n👋 프로그램을 종료합니다.")
            break

        else:
            print("\n❌ 잘못된 선택입니다. 다시 시도하세요.")


def main():
    """메인 함수"""
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("'.env' 파일에 API 키를 설정해주세요.")
        return

    print("\n" + "="*60)
    print("🎯 리뷰 활짝 - 자동 리뷰 생성 시스템")
    print("="*60)

    print("\n실행 모드를 선택하세요:")
    print("1. 전체 리뷰 예제")
    print("2. 빠른 리뷰 예제")
    print("3. 대화형 모드")

    mode = input("\n선택 (1/2/3): ").strip()

    if mode == "1":
        example_full_review()
    elif mode == "2":
        example_quick_review()
    elif mode == "3":
        interactive_mode()
    else:
        print("\n기본 예제를 실행합니다.")
        example_full_review()


if __name__ == "__main__":
    main()