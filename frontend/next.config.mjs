/** @type {import('next').NextConfig} */
const nextConfig = {
  // Pas de limite de taille pour les uploads de fichiers Excel/CSV
  experimental: {
    serverActions: { bodySizeLimit: "50mb" },
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
      {
        source: "/ws/:path*",
        destination: "http://localhost:8001/ws/:path*",
      },
    ];
  },
};

export default nextConfig;
