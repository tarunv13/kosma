/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The engine lives in the Python app. In development Next proxies to it so
  // the browser sees one origin and CORS never enters the picture.
  async rewrites() {
    const api = process.env.KOSMA_API ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "no-referrer" },
          {
            key: "Permissions-Policy",
            value: "geolocation=(), microphone=(), camera=(), payment=()",
          },
        ],
      },
    ];
  },
};
export default nextConfig;
