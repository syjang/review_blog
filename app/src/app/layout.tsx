import type { Metadata } from "next";
import { getSiteUrl } from '@/lib/site';
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = getSiteUrl();

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "리뷰 활짝 - 제품 리뷰 블로그",
    template: "%s | 리뷰 활짝",
  },
  description: "제품들의 솔직한 리뷰를 수집하고 공유합니다. 전자기기, 생활용품, 뷰티, 패션 등 다양한 카테고리의 상품 리뷰.",
  keywords: ["제품 리뷰", "상품 리뷰", "사용기", "구매 후기", "리뷰 활짝"],
  authors: [{ name: "리뷰 활짝" }],
  alternates: {
    canonical: siteUrl,
  },
  icons: {
    icon: '/favicon.svg',
    apple: '/apple-icon.png',
    shortcut: '/favicon.svg',
  },
  openGraph: {
    title: "리뷰 활짝",
    description: "진짜 사용해본 제품들의 솔직한 리뷰",
    url: siteUrl,
    siteName: "리뷰 활짝",
    locale: "ko_KR",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
