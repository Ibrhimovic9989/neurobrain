/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://20.127.80.79:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
