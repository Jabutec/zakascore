import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      { source: "/app", destination: "/workspace", permanent: false },
      { source: "/app/:path*", destination: "/workspace/:path*", permanent: false },
    ];
  },
};

export default nextConfig;
