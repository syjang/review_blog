import { NextResponse } from 'next/server';
import { getAllPosts } from '@/lib/mdx';
import { getSiteUrl } from '@/lib/site';

export async function GET() {
  const siteUrl = getSiteUrl();
  const posts = getAllPosts();

  const items = posts
    .map((post) => {
      const url = `${siteUrl}/blog/${post.slug}`;
      return `
        <item>
          <title><![CDATA[${post.title}]]></title>
          <link>${url}</link>
          <guid>${url}</guid>
          <pubDate>${new Date(post.date).toUTCString()}</pubDate>
          <description><![CDATA[${post.excerpt}]]></description>
        </item>`;
    })
    .join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
  <rss version="2.0">
    <channel>
      <title>리뷰 활짝</title>
      <link>${siteUrl}</link>
      <description>진짜 사용해본 제품들의 솔직한 리뷰</description>
      ${items}
    </channel>
  </rss>`;

  return new NextResponse(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
      'Cache-Control': 's-maxage=3600, stale-while-revalidate',
    },
  });
}


