import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,

  // Explicitly allow dev origins
  allowedDevOrigins: ['http://192.168.1.44:3000', 'http://localhost:3000', '192.168.1.44'], // Use your IP address correctly
};

export default nextConfig;
