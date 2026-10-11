"use client";

import { useEffect } from "react";

const APP_SCOPE = "/workspace";
const APP_CACHE_VERSION = "zakascore-pwa-v3";
const SHELL_READY_KEY = `${APP_CACHE_VERSION}:shell-ready`;

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    // ADDED: development only. In `npm run dev` the worker's cache-first handling of
    // /_next/static can serve stale CSS/JS (old styles coming back, unstyled pages).
    // So in dev we never run the worker, and we remove any worker/caches left from
    // earlier runs. Production builds behave exactly as before.
    if (process.env.NODE_ENV !== "production") {
      void navigator.serviceWorker.getRegistrations().then((registrations) => {
        registrations.forEach((registration) => void registration.unregister());
      });
      if ("caches" in window) {
        void caches.keys().then((keys) => {
          keys
            .filter((key) => key.startsWith("zakascore-pwa-"))
            .forEach((key) => void caches.delete(key));
        });
      }
      return;
    }

    let disposed = false;
    const reloadAfterControl = () => {
      if (disposed || !navigator.serviceWorker.controller) return;
      try {
        if (window.localStorage.getItem(SHELL_READY_KEY) === "true") return;
        window.localStorage.setItem(SHELL_READY_KEY, "true");
        window.location.reload();
      } catch {
        return;
      }
    };

    navigator.serviceWorker.addEventListener("controllerchange", reloadAfterControl);
    async function configureServiceWorker() {
      const registrations = await navigator.serviceWorker.getRegistrations();
      const legacyRootRegistrations = registrations.filter((registration) => {
        const scope = new URL(registration.scope);
        const workers = [registration.active, registration.installing, registration.waiting];
        return (
          scope.origin === window.location.origin &&
          ["/", "/app"].includes(scope.pathname) &&
          workers.some((worker) => worker && new URL(worker.scriptURL).pathname === "/sw.js")
        );
      });
      await Promise.all(legacyRootRegistrations.map((registration) => registration.unregister()));

      await navigator.serviceWorker.register("/sw.js", { scope: APP_SCOPE });
      await navigator.serviceWorker.ready;
      reloadAfterControl();
    }

    void configureServiceWorker().catch((error: unknown) => {
      console.error("PWA service worker setup failed", error);
    });

    return () => {
      disposed = true;
      navigator.serviceWorker.removeEventListener("controllerchange", reloadAfterControl);
    };
  }, []);

  return null;
}