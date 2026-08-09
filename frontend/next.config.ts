import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  compress: true,
  skipTrailingSlashRedirect: true,
};

export default nextConfig;