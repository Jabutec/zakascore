import type { Metadata, Viewport } from "next";
import { PwaRegister } from "./pwa-register";

export const metadata: Metadata = {
  manifest: "/pwa.webmanifest",
  applicationName: "ZakaScore",
  appleWebApp: { capable: true, title: "ZakaScore", statusBarStyle: "default" },
  icons: {
    icon: [{ url: "/icon-192.png", sizes: "192x192", type: "image/png" }],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#ffffff",
  viewportFit: "cover",
};

// Runs before React hydrates, so the browser's install event is never missed.
const captureInstall = `
window.addEventListener("beforeinstallprompt",function(e){
  e.preventDefault();
  window.__zsInstallPrompt=e;
  window.dispatchEvent(new Event("zs-install-available"));
});
window.addEventListener("appinstalled",function(){window.__zsInstallPrompt=undefined;});
`;

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <script dangerouslySetInnerHTML={{ __html: captureInstall }} />
      <PwaRegister />
      {children}
    </>
  );
}