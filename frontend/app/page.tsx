import Link from "next/link";
import type { ReactNode } from "react";
import {
  Check,
  Cpu,
  Download,
  LifeBuoy,
  Lock,
  Mail,
  MessageCircle,
  Upload,
  Wallet,
  Zap,
} from "lucide-react";


const WHATSAPP_URL = "https://wa.me/27735347153";
const SUPPORT_EMAIL = "support@zakascore.co.za";
const elevation =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.04),0_2px_4px_rgba(16,24,40,0.04),0_8px_16px_-4px_rgba(16,24,40,0.06),0_28px_56px_-18px_rgba(16,24,40,0.14)]";
const elevationSm =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.05),0_4px_10px_-2px_rgba(16,24,40,0.07)]";
const glass = `border border-black/[0.07] bg-gradient-to-b from-white/85 to-white/45 backdrop-blur-xl backdrop-saturate-150 ${elevation}`;
const glassInner = `border border-black/[0.06] bg-gradient-to-b from-white/90 to-white/60 backdrop-blur-md ${elevationSm}`;
const iconTile = `flex shrink-0 items-center justify-center rounded-xl border border-[#65a30d]/20 bg-gradient-to-b from-white to-[#ecfccb]/70 text-[#087F55] ${elevationSm}`;
const focusRing =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#087F55]";
const primaryBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-[#65a30d]/40 bg-gradient-to-b from-[#bef264] to-[#A3E635] px-6 py-3 text-sm font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_1px_rgba(16,24,40,0.08),0_8px_20px_-6px_rgba(101,163,13,0.55)] transition hover:brightness-105 active:brightness-95 ${focusRing}`;
const outlineBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-black/10 bg-gradient-to-b from-white to-white/60 px-6 py-3 text-sm font-semibold text-[#0B0F19] backdrop-blur-md ${elevationSm} transition hover:border-[#65a30d]/50 hover:text-[#087F55] ${focusRing}`;


function AmbientBackdrop() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[1200px] overflow-hidden"
    >
      <div className="absolute -left-32 -top-24 h-[520px] w-[520px] rounded-full bg-[#A3E635]/25 blur-[110px]" />
      <div className="absolute -right-24 top-24 h-[480px] w-[480px] rounded-full bg-[#34d399]/20 blur-[110px]" />
      <div className="absolute left-1/3 top-[560px] h-[420px] w-[420px] rounded-full bg-[#A3E635]/15 blur-[120px]" />
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_70%,white)]" />
    </div>
  );
}

function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-black/[0.07] bg-white/70 backdrop-blur-xl backdrop-saturate-150 shadow-[0_1px_0_rgba(255,255,255,0.8),0_8px_24px_-12px_rgba(16,24,40,0.12)]">
      <nav
        aria-label="Main"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <Link
          href="/"
          className={`rounded-md text-xl font-bold tracking-tight text-[#0B0F19] ${focusRing}`}
        >
          Zaka<span className="text-[#087F55]">Score</span>
        </Link>
        <Link href="/login" className={`${primaryBtn} !px-5 !py-2.5`}>
          Launch App
        </Link>
      </nav>
    </header>
  );
}

function ScoreGauge({ score = 712 }: { score?: number }) {
  const pct = (score - 300) / 550;
  const arc = 126;
  return (
    <div className="relative mx-auto h-28 w-48">
      <svg viewBox="0 0 100 56" className="h-full w-full" aria-hidden="true">
        <defs>
          <linearGradient id="zs-gauge" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#4d9a0e" />
            <stop offset="100%" stopColor="#A3E635" />
          </linearGradient>
        </defs>
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="#E5E7EB"
          strokeWidth="8"
          strokeLinecap="round"
        />
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="url(#zs-gauge)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={arc}
          strokeDashoffset={arc * (1 - pct)}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <p className="text-4xl font-bold leading-none tabular-nums text-[#0B0F19]">
          {score}
        </p>
        <p className="mt-1 text-xs font-semibold text-[#087F55]">Strong</p>
      </div>
    </div>
  );
}

function ChatBubble({
  from,
  children,
}: {
  from: "you" | "ai";
  children: ReactNode;
}) {
  const isYou = from === "you";
  return (
    <div className={`flex ${isYou ? "justify-end" : "justify-start"}`}>
      <p
        className={`max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-snug ${
          isYou
            ? "rounded-br-sm border border-[#65a30d]/30 bg-gradient-to-b from-[#bef264] to-[#A3E635] text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_2px_6px_-2px_rgba(101,163,13,0.5)]"
            : `rounded-bl-sm text-slate-700 ${glassInner}`
        }`}
      >
        {children}
      </p>
    </div>
  );
}

function PhoneMockup() {
  return (
    <div
      className="relative mx-auto w-[280px] sm:w-[300px]"
      role="img"
      aria-label="ZakaScore app preview showing a credit score of 712 and a chat to log daily sales"
    >
      <div
        className={`rounded-[2.5rem] border border-black/[0.08] bg-gradient-to-b from-white/80 to-white/40 p-3 backdrop-blur-2xl backdrop-saturate-150 shadow-[inset_0_1px_0_rgba(255,255,255,1),0_2px_4px_rgba(16,24,40,0.05),0_16px_32px_-8px_rgba(16,24,40,0.12),0_48px_80px_-24px_rgba(16,24,40,0.25)]`}
      >
        <div className="mx-auto mb-3 h-1.5 w-16 rounded-full bg-black/10" />

        <div className={`rounded-2xl p-4 ${glassInner}`}>
          <p className="text-xs text-slate-500">Alternative credit score</p>
          <ScoreGauge />
          <div className="mt-3 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg border border-black/[0.06] bg-white/70 py-2">
              <p className="text-sm font-semibold text-[#0B0F19]">R14 820</p>
              <p className="text-[10px] text-slate-500">Weekly turnover</p>
            </div>
            <div className="rounded-lg border border-black/[0.06] bg-white/70 py-2">
              <p className="text-sm font-semibold text-[#0B0F19]">94%</p>
              <p className="text-[10px] text-slate-500">Logged days</p>
            </div>
          </div>
        </div>

        <div className={`mt-3 space-y-2 rounded-2xl p-3 ${glassInner}`}>
          <ChatBubble from="you">Sold R1 250 airtime + R680 snacks today</ChatBubble>
          <ChatBubble from="ai">
            Logged R1 930. That’s your best Tuesday this month.
          </ChatBubble>
          <div className="rounded-full border border-black/[0.08] bg-white/80 px-3 py-2 text-[11px] text-slate-400">
            Log a sale or upload a receipt…
          </div>
        </div>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-14 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-2">
      <div>
        <h1 className="text-4xl font-bold leading-[1.1] tracking-tight text-[#0B0F19] sm:text-5xl lg:text-6xl">
          Your hustle is your credit score.
        </h1>
        <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
          Turn your daily turnover, supplier receipts, and point-of-sale logs
          into a professional credit profile. Powered by secure, zero-latency
          on-device AI.
        </p>
        <div className="mt-8">
          <Link href="/login" className={primaryBtn}>
            <Download className="h-4 w-4" aria-hidden="true" />
            Launch App &amp; Check Score
          </Link>
          <p className="mt-3 text-sm text-slate-500">
            ⚡ Instantly loads offline. Fully private.
          </p>
        </div>
      </div>
      <PhoneMockup />
    </section>
  );
}

const securityBadges: { icon: ReactNode; title: string; text: string }[] = [
  {
    icon: <Lock className="h-5 w-5" aria-hidden="true" />,
    title: "Zero Data Leakage",
    text: "Your logs never leave your phone.",
  },
  {
    icon: <span aria-hidden="true">🇿🇦</span>,
    title: "100% POPIA Compliant",
    text: "Processed entirely client-side.",
  },
  {
    icon: <Zap className="h-5 w-5" aria-hidden="true" />,
    title: "WebGPU Accelerated",
    text: "Lightning-fast, on-device local engine.",
  },
];

function SecurityBar() {
  return (
    <section aria-label="Security and privacy" className="px-4 sm:px-6">
      <ul
        className={`mx-auto grid max-w-6xl divide-y divide-black/[0.07] rounded-2xl md:grid-cols-3 md:divide-x md:divide-y-0 ${glass}`}
      >
        {securityBadges.map((b) => (
          <li key={b.title} className="flex items-start gap-3 p-6">
            <span className={`h-10 w-10 text-lg ${iconTile}`}>{b.icon}</span>
            <div>
              <p className="font-semibold text-[#0B0F19]">{b.title}</p>
              <p className="text-sm text-slate-600">{b.text}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}


const steps = [
  {
    title: "Record your cash business",
    text: "log your daily transactions by sending the a text. Money in, sales, and business activity",
  },
  {
    title: "Build your financial profile",
    text: "ZakaScore analyzes your cash history to understand revenue, transaction activity, consistency, stability, and growth.",
  },
  {
    
    title: "Get your ZakaScore",
    text: "Instantly download an Alternative Credit Score to unlock stock terms, supplier credit, or SMME funding.",
  },
];

function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
      <h2 className="max-w-2xl text-3xl font-bold tracking-tight text-[#0B0F19] sm:text-4xl">
        How Private On-Device AI Works
      </h2>
      <ol className="mt-12 grid gap-6 md:grid-cols-3">
        {steps.map((s, i) => (
          <li
            key={s.title}
            className={`rounded-2xl p-6 motion-safe:transition motion-safe:duration-300 motion-safe:hover:-translate-y-0.5 ${glass}`}
          >
            <div className="flex items-center justify-between">
              <span className="rounded-full border border-black/[0.07] bg-white/70 px-2.5 py-1 text-xs font-medium text-slate-500">
                Step {i + 1}
              </span>
            </div>
            <h3 className="mt-6 text-lg font-semibold text-[#0B0F19]">
              {s.title}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              {s.text}
            </p>
          </li>
        ))}
      </ol>
    </section>
  );
}


type Plan = {
  name: string;
  audience: string;
  price: string;
  features: string[];
  cta: string;
  href: string;
  highlighted?: boolean;
};

const plans: Plan[] = [
  {
    name: "Free",
    audience: "Solo Hustler",
    price: "R0",
    features: [
      "1 connected store",
      "Core local WebLLM financial intelligence",
      "Standard monthly credit passport",
      "100% POPIA secure local processing",
    ],
    cta: "Start Free",
    href: "/login",
  },
  {
    name: "Premium",
    audience: "Growing Business",
    price: "R99",
    features: [
      "Everything in Free",
      "Unlimited multi-stores",
      "Advanced deep-dive intelligence reports",
      "Real-time credit score updates",
      "Priority lender matching",
    ],
    cta: "Go Premium",
    href: "/login",
    highlighted: true,
  },
];

function PlanCard({ plan }: { plan: Plan }) {
  return (
    <article
      className={`relative flex flex-col rounded-2xl p-8 ${
        plan.highlighted
          ? "border border-[#84cc16] bg-gradient-to-b from-[#f7fee7]/95 to-white/60 backdrop-blur-xl backdrop-saturate-150 shadow-[0_0_0_4px_rgba(163,230,53,0.18),inset_0_1px_0_rgba(255,255,255,1),0_2px_4px_rgba(16,24,40,0.05),0_16px_32px_-8px_rgba(101,163,13,0.25),0_40px_72px_-24px_rgba(16,24,40,0.2)]"
          : glass
      }`}
    >
      {plan.highlighted && (
        <span className="absolute -top-3 left-8 rounded-full border border-[#65a30d]/40 bg-gradient-to-b from-[#bef264] to-[#A3E635] px-3 py-1 text-xs font-semibold text-[#0B0F19] shadow-[0_2px_6px_-2px_rgba(101,163,13,0.6)]">
          Most popular
        </span>
      )}
      <h3 className="text-xl font-semibold text-[#0B0F19]">
        {plan.name}{" "}
        <span className="text-base font-normal text-slate-500">
          / {plan.audience}
        </span>
      </h3>
      <p className="mt-4 flex items-baseline gap-1">
        <span className="text-5xl font-bold tracking-tight text-[#0B0F19]">
          {plan.price}
        </span>
        <span className="text-slate-500">/month</span>
      </p>
      <ul className="mt-8 space-y-3 text-sm text-slate-700">
        {plan.features.map((f) => (
          <li key={f} className="flex items-start gap-3">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-[#65a30d]/30 bg-[#ecfccb]">
              <Check className="h-3 w-3 text-[#087F55]" aria-hidden="true" />
            </span>
            {f}
          </li>
        ))}
      </ul>
      <Link
        href={plan.href}
        className={`mt-10 ${plan.highlighted ? primaryBtn : outlineBtn}`}
      >
        {plan.cta}
      </Link>
    </article>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="mx-auto max-w-5xl px-4 py-24 sm:px-6">
      <h2 className="text-3xl font-bold tracking-tight text-[#0B0F19] sm:text-4xl">
        Simple pricing. Start free.
      </h2>
      <p className="mt-3 text-slate-600">
        Upgrade when you add more stores or need lender matching.
      </p>
      <div className="mt-12 grid gap-8 md:grid-cols-2">
        {plans.map((p) => (
          <PlanCard key={p.name} plan={p} />
        ))}
      </div>
    </section>
  );
}

function SupportCard({
  icon,
  title,
  text,
  action,
}: {
  icon: ReactNode;
  title: string;
  text: string;
  action: ReactNode;
}) {
  return (
    <article
      className={`flex flex-col rounded-2xl p-6 motion-safe:transition motion-safe:duration-300 motion-safe:hover:-translate-y-0.5 ${glass}`}
    >
      <span className={`h-12 w-12 ${iconTile}`}>{icon}</span>
      <h3 className="mt-5 text-lg font-semibold text-[#0B0F19]">{title}</h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-slate-600">
        {text}
      </p>
      <div className="mt-6">{action}</div>
    </article>
  );
}

function Support() {
  return (
    <section id="support" className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
      <h2 className="text-3xl font-bold tracking-tight text-[#0B0F19] sm:text-4xl">
        We’ve Got Your Back
      </h2>
      <p className="mt-3 text-slate-600">
        Real local support whenever you need it.
      </p>

      <div className="mt-12 grid gap-6 md:grid-cols-3">
        <SupportCard
          icon={<MessageCircle className="h-6 w-6" aria-hidden="true" />}
          title="WhatsApp Support Chat"
          text="Chat with our team instantly while out trading."
          action={
            <a
              href={WHATSAPP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={`${primaryBtn} w-full`}
            >
              Open WhatsApp
            </a>
          }
        />
        <SupportCard
          icon={<Mail className="h-6 w-6" aria-hidden="true" />}
          title="Email Support"
          text="Need help managing multi-stores or premium billing?"
          action={
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className={`rounded-md font-semibold text-[#087F55] underline-offset-4 hover:underline ${focusRing}`}
            >
              {SUPPORT_EMAIL}
            </a>
          }
        />
        <SupportCard
          icon={<LifeBuoy className="h-6 w-6" aria-hidden="true" />}
          title="Diagnostic Ticket"
          text="Browser acting up or WebGPU error? Open a ticket directly inside your active dashboard."
          action={
            <Link href="/login" className={`${outlineBtn} w-full`}>
              Open Ticket
            </Link>
          }
        />
      </div>
    </section>
  );
}

type FooterLink = { label: string; href: string; external?: boolean };

const footerColumns: { title: string; links: FooterLink[] }[] = [
  {
    title: "Product",
    links: [
      { label: "How it works", href: "/#how-it-works" },
      { label: "Pricing", href: "/#pricing" },
      { label: "Launch App", href: "/login" },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "Documentation", href: "/docs" },
      { label: "Developers", href: "/developers" },
      { label: "Blog", href: "/blog" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Contact", href: "/#support" },
    ],
  },
];

const legalLinks: FooterLink[] = [
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Terms of Service", href: "/terms" },
];

const footerLinkClass = `rounded-md text-sm text-slate-600 transition hover:text-[#087F55] hover:underline underline-offset-4 ${focusRing}`;

function FooterNavLink({ link }: { link: FooterLink }) {
  if (link.external) {
    return (
      <a
        href={link.href}
        target="_blank"
        rel="noopener noreferrer"
        className={footerLinkClass}
      >
        {link.label}
      </a>
    );
  }
  return (
    <Link href={link.href} className={footerLinkClass}>
      {link.label}
    </Link>
  );
}

function Footer() {
  return (
    <footer className="border-t border-black/[0.07] bg-gradient-to-b from-white/60 to-[#f7fee7]/50 backdrop-blur-xl">
      <div className="mx-auto max-w-6xl px-4 pb-8 pt-16 sm:px-6">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_2.6fr]">
          {/* Brand */}
          <div className="max-w-xs">
            <Link
              href="/"
              className={`rounded-md text-xl font-bold tracking-tight text-[#0B0F19] ${focusRing}`}
            >
              Zaka<span className="text-[#087F55]">Score</span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-slate-600">
              Private, on-device credit scoring for South African small
              businesses, traders, and hustlers.
            </p>
          </div>

          {/* Link columns */}
          <nav
            aria-label="Footer"
            className="grid grid-cols-2 gap-8 sm:grid-cols-4"
          >
            {footerColumns.map((col) => (
              <div key={col.title}>
                <h3 className="text-sm font-semibold text-[#0B0F19]">
                  {col.title}
                </h3>
                <ul className="mt-4 space-y-3">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      <FooterNavLink link={link} />
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom bar */}
        <div className="mt-14 flex flex-col gap-4 border-t border-black/[0.07] pt-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
            © {new Date().getFullYear()} ZakaScore. All rights reserved.
          </p>
          <ul className="flex flex-wrap items-center gap-x-6 gap-y-2">
            {legalLinks.map((link) => (
              <li key={link.label}>
                <FooterNavLink link={link} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}

/* --------------------------------- Page ----------------------------------- */

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-x-clip bg-white font-sans text-[#0B0F19] antialiased">
      <AmbientBackdrop />
      <Navbar />
      <main>
        <Hero />
        <SecurityBar />
        <HowItWorks />
        <Pricing />
        <Support />
      </main>
      <Footer />
    </div>
  );
}