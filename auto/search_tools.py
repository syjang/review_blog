"""
웹 검색 도구 모음
제품 리뷰를 위한 최신 정보 검색 및 이미지 검색
"""

from ddgs import DDGS
from typing import List, Dict
import time
from random import uniform
import os



class WebSearcher:
    """웹 검색 도구"""

    def __init__(self):
        # User-Agent 헤더와 타임아웃 설정
        self.delay_range = (2.0, 4.0)  # 요청 간 지연 시간 범위 (증가)
        self.max_retries = 3  # 최대 재시도 횟수

    def _search_with_retry(self, search_func, *args, **kwargs):
        """
        재시도 로직이 포함된 검색 실행
        """
        for attempt in range(self.max_retries):
            try:
                # 첫 번째 시도가 아니면 지연 시간 추가
                if attempt > 0:
                    delay = uniform(*self.delay_range) * (attempt + 1)  # 재시도마다 지연 증가
                    print(f"⏳ {delay:.1f}초 대기 중... (재시도 {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    # 첫 시도에도 약간의 지연 추가
                    time.sleep(uniform(0.5, 1.0))

                # 매번 새로운 DDGS 인스턴스 생성 (세션 초기화)
                with DDGS(timeout=30) as ddgs:
                    results = search_func(ddgs, *args, **kwargs)

                # 성공하면 다음 요청을 위해 지연
                time.sleep(uniform(1.0, 2.0))

                return results

            except Exception as e:
                error_msg = str(e)
                # Rate limit 관련 에러 체크
                if any(x in error_msg.lower() for x in ['ratelimit', 'rate limit', '429', '202']):
                    if attempt < self.max_retries - 1:
                        print(f"⚠️ Rate limit 감지. 재시도 준비중...")
                        continue
                    else:
                        print(f"❌ 최대 재시도 횟수 초과: {e}")
                        return []  # raise 대신 빈 리스트 반환
                # "Exception occurred in previous call" 처리
                elif 'exception occurred in previous call' in error_msg.lower():
                    print(f"⚠️ 이전 호출 오류로 인한 건너뛰기")
                    return []
                else:
                    print(f"❌ 검색 오류: {e}")
                    return []  # raise 대신 빈 리스트 반환

        return []

    def search_product_info(self, product_name: str, max_results: int = 5) -> List[Dict]:
        """
        제품 정보 검색

        Args:
            product_name: 검색할 제품명
            max_results: 최대 결과 수

        Returns:
            검색 결과 리스트
        """
        print(f"🔍 '{product_name}' 검색 중...")

        try:
            # 제품 리뷰 및 사양 검색
            search_query = f"{product_name} 리뷰 사양 특징"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=max_results,
                    region='kr-kr',  # 한국 지역 검색
                    safesearch='moderate'
                ))
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return formatted_results

        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            return []

    def search_product_price(self, product_name: str) -> List[Dict]:
        """
        제품 가격 정보 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            가격 정보 리스트
        """
        print(f"💰 '{product_name}' 가격 검색 중...")

        try:
            # 가격 정보 검색
            search_query = f"{product_name} 가격 최저가"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=3,
                    region='kr-kr'
                ))
            )

            price_info = []
            for result in results:
                price_info.append({
                    "source": result.get("title", ""),
                    "description": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return price_info

        except Exception as e:
            print(f"❌ 가격 검색 오류: {e}")
            return []

    def search_recent_news(self, product_name: str) -> List[Dict]:
        """
        제품 관련 최신 뉴스 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            뉴스 리스트
        """
        print(f"📰 '{product_name}' 뉴스 검색 중...")

        try:
            # 재시도 로직이 포함된 뉴스 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.news(
                    f"{product_name}",
                    max_results=3,
                    region='kr-kr'
                ))
            )

            news = []
            for result in results:
                news.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", ""),
                    "url": result.get("url", "")
                })

            return news

        except Exception as e:
            print(f"❌ 뉴스 검색 오류: {e}")
            return []

    def search_user_reviews(self, product_name: str) -> List[Dict]:
        """
        사용자 리뷰 검색

        Args:
            product_name: 검색할 제품명

        Returns:
            리뷰 정보 리스트
        """
        print(f"⭐ '{product_name}' 사용자 리뷰 검색 중...")

        try:
            # 사용자 리뷰 검색
            search_query = f"{product_name} 사용후기 장단점 실사용"

            # 재시도 로직이 포함된 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.text(
                    search_query,
                    max_results=5,
                    region='kr-kr'
                ))
            )

            reviews = []
            for result in results:
                reviews.append({
                    "title": result.get("title", ""),
                    "summary": result.get("body", ""),
                    "url": result.get("href", "")
                })

            return reviews

        except Exception as e:
            print(f"❌ 리뷰 검색 오류: {e}")
            return []

    def search_product_images(self, product_name: str, max_results: int = 5) -> List[Dict]:
        """
        제품 이미지 검색 (최신 이미지 우선)

        Args:
            product_name: 검색할 제품명
            max_results: 최대 결과 수

        Returns:
            이미지 정보 리스트 (최신순으로 정렬)
        """
        print(f"🖼️ '{product_name}' 최신 이미지 검색 중...")

        try:
            # 최신 이미지를 우선적으로 검색하기 위한 쿼리들
            search_queries = [
                f"{product_name} 2025 제품 사진",  # 최신 연도 우선
                f"{product_name} 2024 제품 사진",
                f"{product_name} 최신 제품 사진",
                f"{product_name} 신제품 이미지",
                f"{product_name} 제품 사진"  # 기본 쿼리
            ]

            all_images = []

            # 여러 쿼리로 검색해서 최신 이미지를 우선 수집
            for i, search_query in enumerate(search_queries[:3]):  # 상위 3개 쿼리만 사용
                print(f"🔍 이미지 검색 쿼리 {i+1}: {search_query}")

                # 재시도 로직이 포함된 이미지 검색
                results = self._search_with_retry(
                    lambda ddgs: list(ddgs.images(
                        search_query,
                        max_results=max_results,
                        region='kr-kr'
                    ))
                )

                for result in results:
                    # 실제 이미지 URL 찾기 (image > thumbnail > url 순서로 우선순위)
                    image_url = result.get("image") or result.get("thumbnail") or result.get("url", "")

                    # 중복 체크 (URL 기준)
                    if not any(img["url"] == image_url for img in all_images):
                        image_info = {
                            "title": result.get("title", ""),
                            "url": image_url,  # 실제 이미지 URL
                            "thumbnail": result.get("thumbnail", ""),
                            "source": result.get("source", ""),
                            "width": result.get("width", 0),
                            "height": result.get("height", 0),
                            "search_query": search_query,  # 어떤 쿼리로 찾았는지 추적
                            "is_recent": "2025" in search_query or "2024" in search_query or "최신" in search_query  # 최신 이미지 표시
                        }
                        all_images.append(image_info)

                # 충분한 이미지를 모았으면 중단
                if len(all_images) >= max_results * 2:
                    break

            # 응답 속도가 빠른 이미지를 우선으로 정렬
            def sort_by_speed(img):
                score = 0
                url = img.get("url", "").lower()

                # 최신 쿼리로 찾은 이미지는 높은 점수
                if img.get("is_recent"):
                    score += 10

                # WebP 형식 우선 (더 빠른 로딩)
                if url.endswith('.webp'):
                    score += 8
                elif url.endswith('.jpg') or url.endswith('.jpeg'):
                    score += 5
                elif url.endswith('.png'):
                    score += 3

                # 알려진 빠른 CDN 호스트 우선
                fast_hosts = [
                    'cloudinary', 'imgur', 'cdn', 'fastly', 'akamai',
                    'googleusercontent', 'githubusercontent', 'amazonaws'
                ]
                if any(host in url for host in fast_hosts):
                    score += 7

                # 너무 큰 이미지는 피함 (파일 크기가 클 가능성)
                width = img.get("width", 0)
                height = img.get("height", 0)
                resolution = width * height

                # 적절한 크기 우선 (너무 작지도 너무 크지도 않게)
                if 200000 < resolution < 2000000:  # 20만~200만 픽셀
                    score += 6
                elif 100000 < resolution <= 200000:  # 10만~20만 픽셀
                    score += 4
                elif resolution <= 100000:  # 너무 작음
                    score += 1

                # 너무 큰 이미지는 감점
                if resolution > 4000000:  # 400만 픽셀 이상
                    score -= 5

                return score

            # 응답 속도 우선순위별로 정렬 후 상위 결과만 반환
            sorted_images = sorted(all_images, key=sort_by_speed, reverse=True)[:max_results]

            print(f"✅ {len(sorted_images)}개 이미지 검색 완료 (최신 우선)")
            return sorted_images

        except Exception as e:
            print(f"❌ 이미지 검색 오류: {e}")
            return []


    def get_comprehensive_info(self, product_name: str) -> Dict:
        """
        제품에 대한 종합 정보 수집 (최신 뉴스 우선)

        Args:
            product_name: 검색할 제품명

        Returns:
            종합 정보 딕셔너리
        """
        print(f"🎯 '{product_name}' 종합 정보 수집 시작...")
        print("="*60)
        print("⚠️ Rate limit 방지를 위해 검색 간 지연 시간이 적용됩니다...")

        # 최신 뉴스를 먼저 검색해서 최신 제품 동향 파악
        print("1️⃣ 최신 뉴스 검색 중...")
        recent_news = self.search_recent_news(product_name)

        # 뉴스 결과를 바탕으로 최신 제품명 업데이트 (예: iPhone 16 → iPhone 16 Pro)
        latest_product_name = product_name
        if recent_news:
            # 뉴스 타이틀에서 최신 제품명 추출 시도
            for news in recent_news[:2]:  # 최근 2개 뉴스만 확인
                news_title = news.get("title", "").lower()
                if any(keyword in news_title for keyword in ["출시", "발표", "공개", "출시일", "스펙"]):
                    # 제품명이 뉴스에 더 구체적으로 나와있을 수 있음
                    latest_product_name = product_name  # 일단은 그대로 사용
                    break

        comprehensive_info = {
            "product": product_name,
            "latest_product": latest_product_name,
            "basic_info": self.search_product_info(latest_product_name),
            "price_info": self.search_product_price(latest_product_name),
            "recent_news": recent_news,
            "user_reviews": self.search_user_reviews(latest_product_name),
            "images": self.search_product_images(latest_product_name)  # 개선된 이미지 검색 사용
        }

        print("="*60)
        print(f"✅ 종합 정보 수집 완료!")
        print(f"📊 수집된 데이터:")
        print(f"  - 뉴스: {len(comprehensive_info['recent_news'])}개")
        print(f"  - 기본 정보: {len(comprehensive_info['basic_info'])}개")
        print(f"  - 가격 정보: {len(comprehensive_info['price_info'])}개")
        print(f"  - 사용자 리뷰: {len(comprehensive_info['user_reviews'])}개")
        print(f"  - 이미지: {len(comprehensive_info['images'])}개")

        return comprehensive_info

    def get_product_images_info(self, product_name: str, images: List[Dict], max_images: int = 3) -> List[Dict]:
        """
        제품 이미지 정보를 수집 (다운로드 없이 링크만)

        Args:
            product_name: 제품명
            images: 이미지 정보 리스트
            max_images: 최대 이미지 수

        Returns:
            이미지 정보 딕셔너리 리스트
        """
        print(f"🔗 '{product_name}' 이미지 링크 수집 중...")

        image_info_list = []
        seen_urls = set()

        # 한글 제품명을 영어로 변환
        safe_product_name = self.translate_korean_product_name(product_name)

        for i, image in enumerate(images[:max_images]):
            if not image.get("url"):
                continue

            # 동일 URL 중복 방지
            if image["url"] in seen_urls:
                continue

            seen_urls.add(image["url"])

            image_info = {
                "id": f"{safe_product_name}-{i+1}",
                "url": image["url"],
                "title": image.get("title", f"{product_name} 제품 이미지 {i+1}"),
                "source": image.get("source", "웹 검색"),
                "is_recent": image.get("is_recent", False),
                "width": image.get("width", 0),
                "height": image.get("height", 0)
            }
            image_info_list.append(image_info)

        print(f"✅ 총 {len(image_info_list)}개 이미지 링크 수집 완료")
        return image_info_list

    def translate_korean_product_name(self, product_name: str) -> str:
        """
        한글 제품명을 영어로 변환

        Args:
            product_name: 한글 제품명

        Returns:
            영어 제품명
        """
        # 한글 제품명을 영어로 매핑하는 딕셔너리
        korean_to_english = {
            # 삼성 제품
            "갤럭시": "galaxy",
            "갤럭시s": "galaxy-s",
            "갤럭시s24": "galaxy-s24",
            "갤럭시s25": "galaxy-s25",
            "갤럭폴드": "galaxy-fold",
            "갤럭폴드7": "galaxy-fold7",
            "버즈프로": "buds-pro",
            "버즈프로3": "buds-pro3",

            # 애플 제품
            "아이폰": "iphone",
            "아이폰16": "iphone-16",
            "아이폰16프로": "iphone-16-pro",
            "아이폰16프로맥스": "iphone-16-pro-max",
            "에어팟": "airpods",
            "에어팟프로": "airpods-pro",
            "애플매직키보드": "apple-magic-keyboard",
            "매직키보드": "magic-keyboard",
            "맥북": "macbook",
            "아이패드": "ipad",
            "애플워치": "apple-watch",

            # 기타 브랜드
            "소니": "sony",
            "소니무선헤드폰": "sony-headphone",
            "다이슨": "dyson",
            "lg": "lg",
            "삼성": "samsung",

            # 일반 단어
            "리뷰": "review",
            "울트라": "ultra",
            "프로": "pro",
            "맥스": "max",
            "미니": "mini",
            "플러스": "+",
            "무선": "wireless",
            "헤드폰": "headphone",
            "키보드": "keyboard",
            "마우스": "mouse",
        }

        # 제품명을 소문자로 변환하고 공백 제거
        safe_name = product_name.lower().replace(" ", "").replace("-", "")

        # 한글을 영어로 변환
        for korean, english in korean_to_english.items():
            safe_name = safe_name.replace(korean, english)

        # 특수문자 제거 및 하이픈으로 변환
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9\-]', '-', safe_name)
        safe_name = re.sub(r'-+', '-', safe_name)  # 연속된 하이픈 제거
        safe_name = safe_name.strip('-')  # 앞뒤 하이픈 제거

        # 빈 문자열이면 기본값 사용
        if not safe_name:
            safe_name = "product"

        return safe_name


def format_search_results(search_data: Dict) -> str:
    """
    검색 결과를 마크다운 형식으로 포맷팅

    Args:
        search_data: 검색 결과 데이터

    Returns:
        포맷팅된 마크다운 문자열
    """
    markdown = f"# {search_data['product']} 검색 결과\n\n"

    # 기본 정보
    if search_data.get("basic_info"):
        markdown += "## 📋 제품 정보\n\n"
        for info in search_data["basic_info"][:3]:
            markdown += f"### {info['title']}\n"
            markdown += f"{info['body']}\n"
            markdown += f"[자세히 보기]({info['url']})\n\n"

    # 가격 정보
    if search_data.get("price_info"):
        markdown += "## 💰 가격 정보\n\n"
        for price in search_data["price_info"]:
            markdown += f"- **{price['source']}**: {price['description']}\n"

    # 최신 뉴스
    if search_data.get("recent_news"):
        markdown += "\n## 📰 최신 뉴스\n\n"
        for news in search_data["recent_news"]:
            markdown += f"- **{news['title']}** ({news.get('date', 'N/A')})\n"
            markdown += f"  {news['body'][:100]}...\n"

    # 사용자 리뷰
    if search_data.get("user_reviews"):
        markdown += "\n## ⭐ 사용자 리뷰\n\n"
        for review in search_data["user_reviews"][:3]:
            markdown += f"- {review['title']}\n"
            markdown += f"  {review['summary'][:100]}...\n"

    return markdown


# 테스트 코드
if __name__ == "__main__":
    searcher = WebSearcher()

    # 테스트할 제품
    test_product = "갤럭시 S24 울트라"

    print(f"🔍 테스트 제품: {test_product}")
    print("-"*60)

    # 종합 정보 수집
    info = searcher.get_comprehensive_info(test_product)

    # 결과 출력
    print("\n📊 수집된 정보:")
    print(f"- 기본 정보: {len(info['basic_info'])}개")
    print(f"- 가격 정보: {len(info['price_info'])}개")
    print(f"- 최신 뉴스: {len(info['recent_news'])}개")
    print(f"- 사용자 리뷰: {len(info['user_reviews'])}개")

    # 마크다운 포맷팅
    markdown_result = format_search_results(info)

    print("\n📝 마크다운 결과 (첫 500자):")
    print(markdown_result[:500])