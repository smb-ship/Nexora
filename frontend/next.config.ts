import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://app-5ece80c1-c79e-4117-be7d-1e54e2ca190f.cleverapps.io/api/:path*",
      },
    ];
  },
};

export default nextConfig;