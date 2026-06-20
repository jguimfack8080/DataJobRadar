/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: false,
  reactStrictMode: true,
  swcMinify: true,
  poweredByHeader: false,
  images: { unoptimized: true },
  experimental: { optimizePackageImports: ['lucide-react', 'recharts'] },
};

module.exports = nextConfig;
