import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Temporarily disabled Turbopack due to issues with Chinese character paths
  // Development environment will automatically fallback to webpack
};

export default nextConfig;