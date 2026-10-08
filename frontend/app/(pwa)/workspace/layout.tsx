import type { Metadata } from "next";
import { PwaRegister } from "./pwa-register";

export const metadata: Metadata = {
  manifest: "/pwa.webmanifest",
};

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PwaRegister />
      {children}
    </>
  );
}