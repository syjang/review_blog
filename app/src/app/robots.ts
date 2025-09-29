import { MetadataRoute } from 'next';
import { getSiteUrl } from '@/lib/site';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = getSiteUrl();
  return {
    rules: [
      {
        userAgent: [
          'Amazonbot',
          'Applebot-Extended',
          'Bytespider',
          'CCBot',
          'ClaudeBot',
          'Google-Extended',
          'GPTBot',
          'meta-externalagent',
        ],
        disallow: '/',
      },
      {
        userAgent: '*',
        allow: '/',
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}