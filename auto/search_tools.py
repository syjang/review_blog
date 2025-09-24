"""
웹 검색 도구 모음
제품 리뷰를 위한 최신 정보 검색 및 이미지 검색
"""

from ddgs import DDGS
from typing import List, Dict
import time
from random import uniform
import os
import requests
import urllib.parse
from PIL import Image
from io import BytesIO



class WebSearcher:
    """웹 검색 도구"""

    def __init__(self):
        # User-Agent 헤더와 타임아웃 설정
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.delay_range = (2.0, 4.0)  # 요청 간 지연 시간 범위 (증가)
        self.max_retries = 3  # 최대 재시도 횟수
        self.image_save_dir = "../app/public/images"  # 이미지 저장 디렉토리

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
        제품 이미지 검색

        Args:
            product_name: 검색할 제품명
            max_results: 최대 결과 수

        Returns:
            이미지 정보 리스트
        """
        print(f"🖼️ '{product_name}' 이미지 검색 중...")

        try:
            # 제품 이미지 검색
            search_query = f"{product_name} 제품 사진"

            # 재시도 로직이 포함된 이미지 검색
            results = self._search_with_retry(
                lambda ddgs: list(ddgs.images(
                    search_query,
                    max_results=max_results,
                    region='kr-kr'
                ))
            )

            images = []
            for result in results:
                # 실제 이미지 URL 찾기 (image > thumbnail > url 순서로 우선순위)
                image_url = result.get("image") or result.get("thumbnail") or result.get("url", "")

                images.append({
                    "title": result.get("title", ""),
                    "url": image_url,  # 실제 이미지 URL
                    "thumbnail": result.get("thumbnail", ""),
                    "source": result.get("source", ""),
                    "width": result.get("width", 0),
                    "height": result.get("height", 0)
                })

            return images

        except Exception as e:
            print(f"❌ 이미지 검색 오류: {e}")
            return []

    def get_image_extension(self, image_url: str, response) -> str:
        """
        이미지 URL과 응답에서 실제 확장자 추출
        모든 이미지를 WebP로 변환하여 저장

        Args:
            image_url: 이미지 URL
            response: HTTP 응답 객체

        Returns:
            이미지 확장자 (항상 'webp')
        """
        # 모든 이미지를 WebP 형식으로 저장
        return 'webp'

    def is_valid_image_response(self, response) -> bool:
        """
        응답이 실제 이미지인지 확인

        Args:
            response: HTTP 응답 객체

        Returns:
            이미지인지 여부
        """
        # Content-Type 확인
        content_type = response.headers.get('content-type', '').lower()
        if not any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']):
            return False

        # Content-Length 확인 (너무 작으면 의심)
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) < 1000:  # 1KB 미만이면 의심
            return False

        return True

    def download_image(self, image_url: str, base_filename: str) -> tuple[bool, str]:
        """
        이미지 다운로드 및 WebP로 변환

        Args:
            image_url: 이미지 URL
            base_filename: 기본 파일명 (확장자 제외)

        Returns:
            (다운로드 성공 여부, 실제 파일명)
        """
        try:
            # 이미지 저장 디렉토리 생성
            os.makedirs(self.image_save_dir, exist_ok=True)

            # 이미지 다운로드
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            # GET 요청으로 이미지 다운로드
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # 실제 이미지인지 확인
            if not self.is_valid_image_response(response):
                print(f"❌ 유효하지 않은 이미지 응답: {image_url}")
                return False, base_filename + ".webp"

            # 이미지를 PIL로 열고 WebP로 변환
            try:
                # 바이트 스트림에서 이미지 열기
                image = Image.open(BytesIO(response.content))

                # RGBA 모드가 아니면 RGB로 변환 (WebP 호환성을 위해)
                if image.mode in ('RGBA', 'LA'):
                    # 투명도가 있는 이미지는 그대로 유지
                    pass
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

                # WebP 파일명 생성
                actual_filename = f"{base_filename}.webp"
                filepath = os.path.join(self.image_save_dir, actual_filename)

                # WebP 형식으로 저장 (품질 85로 설정하여 크기와 품질 균형)
                image.save(filepath, 'WEBP', quality=85, optimize=True)

                print(f"✅ 이미지 저장 완료 (WebP): {filepath}")
                return True, actual_filename

            except Exception as img_error:
                print(f"⚠️ 이미지 변환 실패, 원본으로 저장 시도: {img_error}")

                # PIL 변환 실패시 원본 그대로 저장
                actual_filename = f"{base_filename}.webp"
                filepath = os.path.join(self.image_save_dir, actual_filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"✅ 원본 이미지 저장 완료: {filepath}")
                return True, actual_filename

        except Exception as e:
            print(f"❌ 이미지 다운로드 실패: {e}")
            return False, base_filename + ".webp"

    def get_comprehensive_info(self, product_name: str) -> Dict:
        """
        제품에 대한 종합 정보 수집

        Args:
            product_name: 검색할 제품명

        Returns:
            종합 정보 딕셔너리
        """
        print(f"🎯 '{product_name}' 종합 정보 수집 시작...")
        print("="*60)
        print("⚠️ Rate limit 방지를 위해 검색 간 지연 시간이 적용됩니다...")

        comprehensive_info = {
            "product": product_name,
            "basic_info": self.search_product_info(product_name),
            "price_info": self.search_product_price(product_name),
            "recent_news": self.search_recent_news(product_name),
            "user_reviews": self.search_user_reviews(product_name),
            "images": self.search_product_images(product_name)
        }

        print("="*60)
        print(f"✅ 종합 정보 수집 완료!")

        return comprehensive_info

    def download_product_images(self, product_name: str, images: List[Dict], max_downloads: int = 3) -> List[str]:
        """
        제품 이미지들을 다운로드

        Args:
            product_name: 제품명
            images: 이미지 정보 리스트
            max_downloads: 최대 다운로드 수

        Returns:
            다운로드된 이미지 파일명 리스트
        """
        print(f"📥 '{product_name}' 이미지 다운로드 시작...")

        downloaded_files = []
        # 한글 제품명을 영어로 변환
        safe_product_name = self.translate_korean_product_name(product_name)

        for i, image in enumerate(images[:max_downloads]):
            if not image.get("url"):
                continue

            # 파일명 생성 (확장자 제외)
            base_filename = f"{safe_product_name}-{i+1}"

            # 이미지 다운로드 시도 (실제 확장자 포함)
            success, actual_filename = self.download_image(image["url"], base_filename)
            if success:
                local_path = f"/images/{actual_filename}"
                downloaded_files.append({
                    "filename": actual_filename,
                    "local_path": local_path,
                    "original_url": image["url"],
                    "title": image.get("title", "")
                })

        print(f"✅ 총 {len(downloaded_files)}개 이미지 다운로드 완료")
        return downloaded_files

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