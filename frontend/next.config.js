/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== 'production';

const nextConfig = {
  // Static export only for production builds; dev mode needs rewrites
  ...(isDev ? {} : { output: 'export' }),
  distDir: 'out',
  outputFileTracingRoot: __dirname,
  // Proxy API requests to the backend in dev mode (npm run dev)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
