/** @type {import('next').NextConfig} */

// The client is a static bundle. `next build` writes plain HTML/JS/CSS to
// web/out/, and the FastAPI app serves that directory alongside its own
// /api routes -- one origin, one process, one deploy. Nothing here needs a
// Node server at runtime, so there is no second service to pay for or
// cold-start, and the browser never makes a cross-origin request.
const nextConfig = {
  output: "export",
  reactStrictMode: true,

  // Static export emits <route>/index.html, so the server can resolve a
  // directory request without rewrite rules.
  trailingSlash: true,

  // next/image's default loader needs the Node runtime. Nothing in this UI
  // ships a raster asset -- the chart is SVG and the background is CSS -- so
  // the optimiser is dead weight rather than a loss.
  images: { unoptimized: true },

  // In development Next proxies /api to the Python app so the browser sees a
  // single origin and CORS never enters the picture. `output: export` ignores
  // rewrites, which is correct: in production FastAPI is already serving both
  // the static files and /api from the same origin, so the proxy has nothing
  // left to do.
  async rewrites() {
    const api = process.env.KOSMA_API ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },

  // Security headers used to be declared here. They are set by the FastAPI
  // middleware instead, which is the only thing serving these files in
  // production -- `next build --output export` cannot emit headers, and
  // declaring them in two places invites them to drift apart.
};

export default nextConfig;
