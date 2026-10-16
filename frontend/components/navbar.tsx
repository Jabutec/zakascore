"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";

const links = [
  { label: "Solution", href: "/#solution" },
  { label: "How It Works", href: "/#how-it-works" },
  { label: "Features", href: "/#features" },
  { label: "FAQ", href: "/#faq" },
];

const focusRing =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#4d7c0f]";

const darkBtn = `inline-flex items-center justify-center rounded-full bg-[#CC5500] px-5 py-2 text-sm font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_1px_2px_rgba(16,24,40,0.2)] transition hover:bg-[#b34a00] ${focusRing}`;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);

  return (
    <header className="pointer-events-none fixed inset-x-0 top-3 z-50 px-3 sm:top-4 sm:px-6">
      <div className="relative mx-auto max-w-6xl">
        <nav
          aria-label="Main"
          className="pointer-events-auto flex h-14 items-center justify-between rounded-full border border-white/60 bg-white/55 pl-4 pr-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_8px_24px_-8px_rgba(16,24,40,0.18)] backdrop-blur-xl backdrop-saturate-150 sm:pl-6 md:grid md:grid-cols-[1fr_auto_1fr] md:pr-2.5"
        >
          {/* Logo + name */}
          <Link href="/" onClick={close} aria-label="ZakaScore home" className={`flex items-center gap-2 rounded-full ${focusRing}`}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="" className="h-8 w-8 object-contain" />
            <span className="text-lg font-semibold tracking-tight text-[#0B0F19]">
              Zaka<span className="text-[#4d7c0f]">Score</span>
            </span>
          </Link>

          {/* Desktop: links in the middle */}
          <ul className="hidden items-center gap-8 md:flex">
            {links.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className={`rounded-full text-sm font-medium text-[#0B0F19]/80 transition hover:text-[#4d7c0f] ${focusRing}`}
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>

          {/* Desktop: Login + Get Started on the far side */}
          <div className="hidden items-center gap-5 justify-self-end md:flex">
            <Link href="/login" className={`rounded-full text-sm font-semibold text-[#0B0F19] transition hover:text-[#4d7c0f] ${focusRing}`}>
              Login
            </Link>
            <Link href="/signup" className={darkBtn}>
              Get Started
            </Link>
          </div>

          {/* Mobile: hamburger */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            className={`flex h-10 w-10 items-center justify-center rounded-full text-[#0B0F19] transition hover:bg-black/5 md:hidden ${focusRing}`}
          >
            {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
        </nav>

        {/* Mobile menu panel */}
        {open && (
          <div
            id="mobile-menu"
            className="pointer-events-auto absolute inset-x-0 top-[calc(3.5rem+0.5rem)] rounded-3xl border border-white/60 bg-white/90 p-3 shadow-[0_16px_40px_-12px_rgba(16,24,40,0.25)] md:hidden"
          >
            <ul>
              {links.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    onClick={close}
                    className={`block rounded-2xl px-4 py-3 text-base font-medium text-[#0B0F19] transition hover:bg-[#f7fee7] ${focusRing}`}
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="mt-2 grid grid-cols-2 gap-2 border-t border-black/[0.08] pt-3">
              <Link
                href="/login"
                onClick={close}
                className={`inline-flex items-center justify-center rounded-full border border-black/10 bg-white py-2.5 text-sm font-semibold text-[#0B0F19] ${focusRing}`}
              >
                Login
              </Link>
              <Link href="/signup" onClick={close} className={`${darkBtn} !py-2.5`}>
                Get Started
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}