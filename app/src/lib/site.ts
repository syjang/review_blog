export function getSiteUrl(): string {
  // 환경변수 우선, 없으면 요청하신 도메인으로 고정
  const url = process.env.NEXT_PUBLIC_SITE_URL || 'https://reviewda.com';
  return url.replace(/\/$/, '');
}


