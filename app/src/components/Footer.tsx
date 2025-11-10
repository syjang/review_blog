export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 text-slate-300 py-12 mt-20">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-white font-bold text-lg mb-4">리뷰 활짝</h3>
            <p className="text-sm leading-relaxed">
              세상의 모든 제품을 리뷰하는 블로그입니다.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">연락처</h4>
            <div className="space-y-2 text-sm">
              <p>jattacker7@gmail.com</p>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-700 mt-8 pt-8 text-center">
          <div className="mb-3 space-x-4 text-sm">
            <a className="hover:text-white" href="/about">
              소개
            </a>
            <a className="hover:text-white" href="/contact">
              연락처
            </a>
            <a className="hover:text-white" href="/privacy-policy">
              개인정보처리방침
            </a>
            <a className="hover:text-white" href="/review-policy">
              리뷰 정책
            </a>
          </div>
          <p className="text-sm text-slate-400">
            © {currentYear} 리뷰 활짝. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
