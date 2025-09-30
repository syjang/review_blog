import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.it.chosun.com',
      },
      {
        protocol: 'https',
        hostname: 'imgnews.pstatic.net',
      },
      {
        protocol: 'https',
        hostname: 'img.sbs.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'image.ytn.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'dimg.donga.com',
      },
      {
        protocol: 'https',
        hostname: 'img.khan.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'cdn.jtbc.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'img.hani.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'image.mt.co.kr',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'i.imgur.com',
      },
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: 'images.pexels.com',
      },
      {
        protocol: 'https',
        hostname: 'cdn.pixabay.com',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
      },
      {
        protocol: 'https',
        hostname: '*.daumcdn.net',
      },
      {
        protocol: 'https',
        hostname: '*.naver.com',
      },
    ],
  },
};

export default nextConfig;
