/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/codeatlas/:path*",
        destination: "http://app:5000/:path*",
      },
    ]
  },
}

module.exports = nextConfig
