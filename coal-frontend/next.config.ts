import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/:path*", // 确保用 IPv4
      },
    ];
  },
};

export default nextConfig;
