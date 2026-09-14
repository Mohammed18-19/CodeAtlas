/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/codeatlas/:path*",
        destination:
          process.env.CODEATLAS_BACKEND_URL || "http://localhost:5000/:path*",
      },
    ]
  },
}

module.exports = nextConfig
