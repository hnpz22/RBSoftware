/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['react-pdf-highlighter', 'pdfjs-dist'],
  webpack: (config) => {
    // Prevent pdfjs-dist pdf_viewer from being split into a separate chunk
    // that Next.js dev server can't map to a URL (causes /_next/undefined)
    config.module.rules.push({
      test: /pdfjs-dist[/\\]web[/\\]pdf_viewer/,
      sideEffects: true,
    });
    return config;
  },
};

export default nextConfig;
