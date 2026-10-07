import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/app",
    name: "ZakaScore",
    short_name: "ZakaScore",
    description: "Financial intelligence for your business.",
    start_url: "/app",
    scope: "/",
    display: "standalone",
    background_color: "#f9fafb",
    theme_color: "#111827",
    icons: [
      {
        src: "/zakascore.png",
        sizes: "any",
        type: "image/png",
      },
    ],
  };
}
