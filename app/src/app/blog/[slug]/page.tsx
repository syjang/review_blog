import { getPostBySlug, getAllPosts, markdownToHtml } from "@/lib/mdx";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Script from "next/script";
import Link from "next/link";
import Image from "next/image";
import { getSiteUrl } from "@/lib/site";
import "./prism.css";

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateStaticParams() {
  const posts = getAllPosts();
  return posts.map((post) => ({
    slug: post.slug,
  }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getPostBySlug(slug);

  if (!post) {
    return {
      title: "포스트를 찾을 수 없습니다",
    };
  }

  const siteUrl = getSiteUrl();
  const url = `${siteUrl}/blog/${post.slug}`;
  return {
    title: `${post.title} | 리뷰 활짝`,
    description: post.excerpt,
    alternates: { canonical: url },
    robots: post.noindex
      ? { index: false, follow: true }
      : { index: true, follow: true },
    openGraph: {
      title: post.title,
      description: post.excerpt,
      url,
      type: "article",
      publishedTime: post.date,
      modifiedTime: post.updated || post.date,
      authors: ["리뷰 활짝"],
      images: post.coverImage ? [post.coverImage] : [],
    },
  };
}

export default async function PostPage({ params }: Props) {
  const { slug } = await params;
  const post = getPostBySlug(slug);

  if (!post) {
    notFound();
  }

  const content = await markdownToHtml(post.content);
  const siteUrl = getSiteUrl();
  const url = `${siteUrl}/blog/${post.slug}`;
  const allPosts = getAllPosts();
  const related = allPosts
    .filter(
      (p) => p.slug !== post.slug && p.tags?.some((t) => post.tags?.includes(t))
    )
    .slice(0, 3);

  // FAQ 추출 (markdown의 "### FAQ" 섹션에서 간단 파싱)
  const faqRaw = (() => {
    const marker = "### FAQ";
    const idx = post.content.indexOf(marker);
    if (idx === -1) return "";
    const after = post.content.slice(idx + marker.length);
    const nextIdx = after.indexOf("### ");
    return (nextIdx === -1 ? after : after.slice(0, nextIdx)).trim();
  })();

  const faqItems = (() => {
    const items: { q: string; a: string }[] = [];
    if (!faqRaw) return items;
    const lines = faqRaw.split("\n");
    let i = 0;
    const isQuestion = (s: string) =>
      /(^[-*]\s*)?(Q[:).]\s*|질문[:]\s*|.+\?\s*$)/i.test(s.trim());
    while (i < lines.length) {
      const line = lines[i].trim();
      if (!line) {
        i++;
        continue;
      }
      if (isQuestion(line)) {
        const q = line
          .replace(/^[-*]\s*/, "")
          .replace(/^(Q[:).]|질문:)\s*/i, "")
          .trim();
        let j = i + 1;
        const answerLines: string[] = [];
        while (j < lines.length && lines[j].trim() && !isQuestion(lines[j])) {
          answerLines.push(lines[j].trim());
          j++;
        }
        const a = answerLines.join(" ");
        if (q && a) items.push({ q, a });
        i = j;
      } else {
        i++;
      }
    }
    return items.slice(0, 6);
  })();

  return (
    <article className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Script id="review-jsonld" type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "Review",
          itemReviewed: {
            "@type": "Thing",
            name: post.title,
          },
          author: { "@type": "Person", name: post.author || "리뷰 활짝" },
          datePublished: post.date,
          dateModified: post.updated || post.date,
          reviewRating: { "@type": "Rating", ratingValue: post.rating || 4 },
          url,
        })}
      </Script>
      <Script id="breadcrumb-jsonld" type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "BreadcrumbList",
          itemListElement: [
            { "@type": "ListItem", position: 1, name: "Home", item: siteUrl },
            { "@type": "ListItem", position: 2, name: post.title, item: url },
          ],
        })}
      </Script>
      {faqItems.length > 0 && (
        <Script id="faq-jsonld" type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            mainEntity: faqItems.map((it) => ({
              "@type": "Question",
              name: it.q,
              acceptedAnswer: { "@type": "Answer", text: it.a },
            })),
          })}
        </Script>
      )}
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <header className="mb-12">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 mb-6 leading-tight">
            {post.title}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-gray-600 mb-6">
            <time dateTime={post.date} className="text-base">
              {new Date(post.date).toLocaleDateString("en-CA", {
                timeZone: "UTC",
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
              })}
            </time>
            <span className="text-gray-400">·</span>
            <span>{post.readingTime}</span>
            {post.rating && (
              <>
                <span className="text-gray-400">·</span>
                <span className="flex items-center gap-1">
                  <span className="text-yellow-500">★</span>
                  <span>{post.rating}/5</span>
                </span>
              </>
            )}
          </div>

          {post.tags && post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-8">
              {post.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 text-sm font-medium text-blue-700 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          <div className="text-sm text-gray-500 mb-4">
            <span>작성자: {post.author || "리뷰 활짝"}</span>
            {post.updated && (
              <>
                <span className="mx-2">·</span>
                <span>
                  업데이트: {new Date(post.updated).toLocaleDateString("ko-KR")}
                </span>
              </>
            )}
          </div>

          {post.coverImage && (
            <div className="mb-8 rounded-xl overflow-hidden shadow-lg">
              <div className="relative aspect-video">
                <Image
                  src={post.coverImage}
                  alt={post.title}
                  fill
                  sizes="(max-width: 768px) 100vw, 800px"
                  className="object-cover"
                  priority={false}
                />
              </div>
            </div>
          )}
        </header>

        <div
          className="prose prose-lg max-w-none"
          dangerouslySetInnerHTML={{ __html: content }}
        />

        <footer className="mt-16 pt-8 border-t border-gray-200">
          {related.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">
                관련 글
              </h3>
              <ul className="space-y-2">
                {related.map((r) => (
                  <li key={r.slug}>
                    <Link
                      className="text-blue-600 hover:text-blue-700"
                      href={`/blog/${r.slug}`}
                    >
                      {r.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex justify-between items-center">
            <Link
              href="/"
              className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              <svg
                className="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              목록으로 돌아가기
            </Link>
          </div>
        </footer>
      </div>
    </article>
  );
}
