import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowRight,
  BarChart3,
  Banknote,
  EyeOff,
  FileQuestion,
  Mail,
  MessageCircle,
  Receipt,
  ShieldCheck,
  Smartphone,
  Users,
  WifiOff,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { Reveal } from "@/components/reveal";

const WHATSAPP_URL = "https://wa.me/27735347153";
const SUPPORT_EMAIL = "support@zakascore.co.za";

/* -------------------------------------------------------------------------- */
/*  Look: white page, glossy lime buttons, hairline borders, neutral shadows. */
/*  Lime #A3E635 for fills (dark text on top); #4d7c0f for lime-toned text.   */
/* -------------------------------------------------------------------------- */

const elevation =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.04),0_2px_4px_rgba(16,24,40,0.04),0_8px_16px_-4px_rgba(16,24,40,0.06),0_28px_56px_-18px_rgba(16,24,40,0.14)]";
const elevationSm =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.05),0_4px_10px_-2px_rgba(16,24,40,0.07)]";
const glass = `border border-black/[0.07] bg-gradient-to-b from-white/90 to-white/60 backdrop-blur-xl backdrop-saturate-150 ${elevation}`;
const glassInner = `border border-black/[0.06] bg-gradient-to-b from-white/90 to-white/60 backdrop-blur-md ${elevationSm}`;
const iconTile = `flex shrink-0 items-center justify-center rounded-xl border border-[#65a30d]/20 bg-[#f7fee7] text-[#4d7c0f] ${elevationSm}`;
const focusRing =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#4d7c0f]";

const primaryBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-[#65a30d]/50 bg-gradient-to-b from-[#bef264] to-[#A3E635] px-6 py-3 text-sm font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_2px_rgba(16,24,40,0.12)] transition hover:brightness-105 active:brightness-95 ${focusRing}`;
const outlineBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-black/10 bg-gradient-to-b from-white to-white/60 px-6 py-3 text-sm font-semibold text-[#0B0F19] ${elevationSm} transition hover:border-[#65a30d]/50 hover:text-[#4d7c0f] ${focusRing}`;
const inkBtn = `inline-flex items-center justify-center gap-2 rounded-xl bg-[#0B0F19] px-6 py-3 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(16,24,40,0.2)] transition hover:bg-[#1f2937] ${focusRing}`;

function SectionHeading({ title, text }: { title: string; text?: string }) {
  return (
    <div className="max-w-2xl">
      <h2 className="text-3xl font-semibold tracking-tight text-[#0B0F19] sm:text-4xl">{title}</h2>
      {text && <p className="mt-3 text-base leading-relaxed text-slate-600">{text}</p>}
    </div>
  );
}

/* -------------------------------- Navbar ---------------------------------- */

function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-black/[0.07] bg-white/80 backdrop-blur-xl backdrop-saturate-150">
      <nav aria-label="Main" className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
        <Link href="/" className={`rounded-md text-xl font-semibold tracking-tight text-[#0B0F19] ${focusRing}`}>
          Zaka<span className="text-[#4d7c0f]">Score</span>
        </Link>

        <div className="flex items-center gap-3 sm:gap-5">
          <Link
            href="/login"
            className={`rounded-md text-sm font-medium text-[#0B0F19] transition hover:text-[#4d7c0f] ${focusRing}`}
          >
            Sign In
          </Link>
          <Link href="/signup" className={`${primaryBtn} !px-5 !py-2.5`}>
            Get Started
          </Link>
        </div>
      </nav>
    </header>
  );
}

/* ------------------------------ Phone mockup ------------------------------ */

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
        <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="#E5E7EB" strokeWidth="8" strokeLinecap="round" />
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
        <p className="text-4xl font-semibold leading-none tabular-nums text-[#0B0F19]">{score}</p>
        <p className="mt-1 text-xs font-semibold text-[#4d7c0f]">Strong</p>
      </div>
    </div>
  );
}

function ChatBubble({ from, children }: { from: "you" | "ai"; children: ReactNode }) {
  const isYou = from === "you";
  return (
    <div className={`flex ${isYou ? "justify-end" : "justify-start"}`}>
      <p
        className={`max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-snug ${
          isYou
            ? "rounded-br-sm border border-[#65a30d]/40 bg-gradient-to-b from-[#bef264] to-[#A3E635] text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.5),0_1px_2px_rgba(16,24,40,0.1)]"
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
      <div className="rounded-[2.5rem] border border-black/[0.08] bg-gradient-to-b from-white/90 to-white/50 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,1),0_2px_4px_rgba(16,24,40,0.05),0_16px_32px_-8px_rgba(16,24,40,0.12),0_48px_80px_-24px_rgba(16,24,40,0.25)]">
        <div className="mx-auto mb-3 h-1.5 w-16 rounded-full bg-black/10" />

        <div className={`rounded-2xl p-4 ${glassInner}`}>
          <p className="text-xs text-slate-500">Alternative credit score</p>
          <ScoreGauge />
          <div className="mt-3 grid grid-cols-2 gap-2 text-center">
            <div className="rounded-lg border border-black/[0.06] bg-white/80 py-2">
              <p className="text-sm font-semibold text-[#0B0F19]">R14 820</p>
              <p className="text-[10px] text-slate-500">Weekly turnover</p>
            </div>
            <div className="rounded-lg border border-black/[0.06] bg-white/80 py-2">
              <p className="text-sm font-semibold text-[#0B0F19]">94%</p>
              <p className="text-[10px] text-slate-500">Logged days</p>
            </div>
          </div>
        </div>

        <div className={`mt-3 space-y-2 rounded-2xl p-3 ${glassInner}`}>
          <ChatBubble from="you">Sold R1 250 airtime + R680 snacks today</ChatBubble>
          <ChatBubble from="ai">Logged R1 930. That’s your best Tuesday this month.</ChatBubble>
          <div className="rounded-full border border-black/[0.08] bg-white/80 px-3 py-2 text-[11px] text-slate-400">
            Log a sale or upload a receipt…
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------ 1. Hero ----------------------------------- */

function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 text-center sm:px-6 md:py-24 lg:grid-cols-2 lg:gap-14 lg:text-left">
      <div className="motion-safe:animate-[rise_0.7s_cubic-bezier(0.22,0.61,0.36,1)_both]">
        <h1 className="text-balance text-4xl font-semibold leading-[1.1] tracking-tight text-[#0B0F19] sm:text-5xl lg:text-6xl">
          Your Hustle Is Your Credit Score.
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg lg:mx-0">
          Turn your daily sales into a credit profile that lenders and suppliers can trust. Log sales like a text
          message, and let private on-device AI do the rest.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-center lg:justify-start">
          <Link href="/signup" className={`${primaryBtn} w-full sm:w-auto`}>
            Get Started
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link href="/#how-it-works" className={`${outlineBtn} w-full sm:w-auto`}>
            See How It Works
          </Link>
        </div>
        <p className="mt-4 text-sm text-slate-500">⚡ Loads instantly, even offline. Your messages stay on your device.</p>
      </div>

      {/* On phones the mockup is cropped and faded at the bottom so it doesn't push the page down */}
      <div className="relative mx-auto max-h-[430px] w-full overflow-hidden [-webkit-mask-image:linear-gradient(to_bottom,black_75%,transparent)] [mask-image:linear-gradient(to_bottom,black_75%,transparent)] motion-safe:animate-[rise_0.8s_cubic-bezier(0.22,0.61,0.36,1)_0.15s_both] md:max-h-none md:overflow-visible md:[-webkit-mask-image:none] md:[mask-image:none]">
        <PhoneMockup />
      </div>
    </section>
  );
}

/* ---------------- Trust strip (sits where "companies" would go) ------------- */

const trustPoints: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: Zap, title: "On-Device AI", text: "Your messages are read on your phone, not in the cloud." },
  { icon: WifiOff, title: "Works Offline", text: "Log sales without data. They sync when you reconnect." },
  { icon: ShieldCheck, title: "You Stay In Control", text: "Only the sales you confirm are saved to your account." },
];

function TrustStrip() {
  return (
    <section aria-label="Why people trust ZakaScore" className="px-4 sm:px-6">
      <Reveal>
        <ul
          className={`mx-auto grid max-w-6xl divide-y divide-black/[0.07] rounded-2xl md:grid-cols-3 md:divide-x md:divide-y-0 ${glass}`}
        >
          {trustPoints.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex items-start gap-3 p-6">
              <span className={`h-10 w-10 ${iconTile}`}>
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <p className="font-semibold text-[#0B0F19]">{title}</p>
                <p className="text-sm text-slate-600">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </Reveal>
    </section>
  );
}

/* ------------------------ 2. Problem / agitation -------------------------- */

const problems: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: FileQuestion,
    title: "No Payslip, No Credit",
    text: "Lenders ask for payslips and formal statements. A trader, hairdresser or spaza owner often has neither, so the answer is no before anyone looks at the business.",
  },
  {
    icon: Receipt,
    title: "Cash Leaves No Trail",
    text: "Daily sales, airtime and stock purchases end up in your head or a notebook. Without a record, it is hard to prove how well the business really runs.",
  },
  {
    icon: EyeOff,
    title: "Sharing Your Numbers Feels Risky",
    text: "Many tools want your sales and receipts on someone else’s servers. Your numbers are your business, and not everyone is comfortable handing them over.",
  },
];

function Problem() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
      <Reveal>
        <SectionHeading
          title="Your Business Is Real. Your Paper Trail Isn’t."
          text="Plenty of South African businesses are doing well and still get turned away. Here’s why."
        />
      </Reveal>
      <ul className="mt-12 grid gap-6 md:grid-cols-3">
        {problems.map(({ icon: Icon, title, text }, index) => (
          <Reveal as="li" key={title} delay={index * 100} className={`rounded-2xl p-6 ${glass}`}>
            <span className={`h-12 w-12 ${iconTile}`}>
              <Icon className="h-6 w-6" aria-hidden="true" />
            </span>
            <h3 className="mt-5 text-lg font-semibold text-[#0B0F19]">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{text}</p>
          </Reveal>
        ))}
      </ul>
    </section>
  );
}

/* ----------------------------- 3. Solution -------------------------------- */

function CreditPassportCard() {
  const signals = [
    ["Revenue trend", "Growing"],
    ["Cash-flow consistency", "Steady"],
    ["Business activity", "Active"],
  ];
  return (
    <div className={`mx-auto w-full max-w-md rounded-3xl p-6 ${glass}`}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-[#0B0F19]">ZakaScore</p>
        <span className="rounded-full border border-black/[0.07] bg-white/80 px-2.5 py-1 text-xs text-slate-500">
          Sample preview
        </span>
      </div>
      <div className="mt-4">
        <ScoreGauge score={712} />
      </div>
      <dl className="mt-6 divide-y divide-black/[0.07] border-t border-black/[0.07]">
        {signals.map(([label, value]) => (
          <div key={label} className="flex items-center justify-between py-3 text-sm">
            <dt className="text-slate-600">{label}</dt>
            <dd className="font-semibold text-[#0B0F19]">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function Solution() {
  return (
    <section id="solution" className="mx-auto grid max-w-6xl scroll-mt-24 items-center gap-14 px-4 py-24 sm:px-6 lg:grid-cols-2">
      <Reveal>
        <CreditPassportCard />
      </Reveal>
      <Reveal delay={120}>
        <h2 className="text-3xl font-semibold tracking-tight text-[#0B0F19] sm:text-4xl">
          Turn Everyday Sales Into a Credit Profile That Speaks for You
        </h2>
        <p className="mt-4 text-base leading-relaxed text-slate-600">
          Tell ZakaScore about each sale the way you would text a friend. It builds a clear picture of your revenue,
          consistency and growth, then turns it into an Alternative Credit Score you can take to suppliers and
          lenders.
        </p>
        <p className="mt-3 text-base leading-relaxed text-slate-600">
          The AI that reads your messages runs on your own phone, so you are never feeding a cloud chatbot.
        </p>
        <div className="mt-8">
          <Link href="/signup" className={primaryBtn}>
            Check Your Score
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>
      </Reveal>
    </section>
  );
}

/* ----------------------- 4. Features / benefits --------------------------- */

const features: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: Banknote,
    title: "Get Credit Without a Payslip",
    text: "An Alternative Credit Score built from your real daily sales.",
  },
  {
    icon: Smartphone,
    title: "Log a Sale in Seconds",
    text: "Type it like a text: “2 shirts, R300, cash”. Review it, confirm it, done.",
  },
  {
    icon: WifiOff,
    title: "Keep Trading Without Data",
    text: "Installs like an app and works offline. Sales sync automatically when you reconnect.",
  },
  {
    icon: ShieldCheck,
    title: "Keep Your Messages Private",
    text: "On-device AI reads what you type, so it never goes to a cloud chatbot.",
  },
  {
    icon: BarChart3,
    title: "See What Is Working",
    text: "Revenue trends, top sellers and payment channels in one clean dashboard.",
  },
  {
    icon: Users,
    title: "Bring Your Team Along",
    text: "Invite staff with one-time codes and keep every store in one place.",
  },
];

function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-24 sm:px-6">
      <div className="grid gap-12 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="lg:sticky lg:top-28 lg:self-start">
          <Reveal>
            <SectionHeading
              title="Everything You Need to Get Credit-Ready"
              text="Built for busy days on the floor, the street or the stall, not for accountants."
            />
            <div className="mt-8">
              <Link href="/signup" className={outlineBtn}>
                Get Started
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          </Reveal>
        </div>

        <ul className="grid gap-4 sm:grid-cols-2">
          {features.map(({ icon: Icon, title, text }, index) => (
            <Reveal as="li" key={title} delay={(index % 2) * 90} className="h-full">
              <div
                className={`h-full rounded-2xl p-5 motion-safe:transition motion-safe:duration-300 motion-safe:hover:-translate-y-0.5 ${glass}`}
              >
                <span className={`h-10 w-10 ${iconTile}`}>
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-[#0B0F19]">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{text}</p>
              </div>
            </Reveal>
          ))}
        </ul>
      </div>
    </section>
  );
}

/* ---------------------------- 5. How it works ----------------------------- */

const steps = [
  {
    title: "Record Your Cash Business",
    text: "Log your daily transactions by sending a text. Money in, sales and business activity.",
  },
  {
    title: "Build Your Financial Profile",
    text: "ZakaScore analyzes your cash history to understand revenue, transaction activity, consistency, stability and growth.",
  },
  {
    title: "Get Your ZakaScore",
    text: "Instantly download an Alternative Credit Score to unlock stock terms, supplier credit or SMME funding.",
  },
];

function ChatPreview() {
  return (
    <div className={`mx-auto w-full max-w-md rounded-3xl p-5 ${glass}`}>
      <div className="space-y-3">
        <ChatBubble from="you">Sold 3 airtime vouchers, R150 total, cash</ChatBubble>
        <ChatBubble from="ai">I understood R150.00, paid cash. Is that right?</ChatBubble>
        <div className={`rounded-2xl p-4 ${glassInner}`}>
          <p className="text-xs text-slate-500">Review sale</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-[#0B0F19]">R150.00</p>
          <p className="text-xs text-slate-500">3 × airtime voucher · Paid by cash</p>
          <div className="mt-3 flex items-center justify-center rounded-xl border border-[#65a30d]/50 bg-gradient-to-b from-[#bef264] to-[#A3E635] py-2 text-xs font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_2px_rgba(16,24,40,0.12)]">
            Confirm and Record
          </div>
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto grid max-w-6xl scroll-mt-24 items-center gap-14 px-4 py-24 sm:px-6 lg:grid-cols-2">
      <div>
        <Reveal>
          <SectionHeading title="From Daily Sales to Credit Score in 3 Steps" />
        </Reveal>
        <ol className="mt-10 space-y-8">
          {steps.map((step, index) => (
            <Reveal as="li" key={step.title} delay={index * 120} className="flex gap-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#65a30d]/50 bg-gradient-to-b from-[#bef264] to-[#A3E635] text-sm font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_2px_rgba(16,24,40,0.12)]">
                {index + 1}
              </span>
              <div>
                <h3 className="text-lg font-semibold text-[#0B0F19]">{step.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">{step.text}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </div>
      <Reveal delay={150}>
        <ChatPreview />
      </Reveal>
    </section>
  );
}

/* -------------------------- 6. Objection handling ------------------------- */

const objections: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: ShieldCheck,
    title: "Is My Data Safe?",
    text: "The AI reads your messages on your own device, not on a cloud chatbot. Only the sale you confirm is saved to your account, and you review every sale before it is recorded.",
  },
  {
    icon: Smartphone,
    title: "Do I Need Data or a New Phone?",
    text: "ZakaScore installs like an app and keeps working offline. The on-device assistant needs a recent browser with WebGPU. Without it, you can still type your sales and review them before saving.",
  },
  {
    icon: Banknote,
    title: "Will Lenders Take It Seriously?",
    text: "Your score comes from real sales history, so you can show a track record instead of a promise. Every lender decides for itself, so treat it as strong supporting evidence, not a guarantee.",
  },
];

function Objections() {
  return (
    <section id="faq" className="mx-auto max-w-6xl scroll-mt-24 px-4 py-24 sm:px-6">
      <Reveal>
        <SectionHeading title="Questions You Might Have" />
      </Reveal>
      <ul className="mt-12 grid gap-6 md:grid-cols-3">
        {objections.map(({ icon: Icon, title, text }, index) => (
          <Reveal as="li" key={title} delay={index * 100} className={`rounded-2xl p-6 ${glass}`}>
            <span className={`h-10 w-10 ${iconTile}`}>
              <Icon className="h-5 w-5" aria-hidden="true" />
            </span>
            <h3 className="mt-4 text-lg font-semibold text-[#0B0F19]">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{text}</p>
          </Reveal>
        ))}
      </ul>

      <Reveal className="mt-6">
        <div className={`flex flex-col gap-4 rounded-2xl p-6 sm:flex-row sm:items-center sm:justify-between ${glass}`}>
          <div>
            <p className="font-semibold text-[#0B0F19]">Still unsure? Talk to a real person.</p>
            <p className="mt-1 text-sm text-slate-600">
              Chat with us on WhatsApp, or open a ticket from inside your dashboard if something misbehaves.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <a href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer" className={outlineBtn}>
              <MessageCircle className="h-4 w-4" aria-hidden="true" />
              Open WhatsApp
            </a>
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className={`inline-flex items-center gap-2 rounded-md text-sm font-semibold text-[#4d7c0f] underline-offset-4 hover:underline ${focusRing}`}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              {SUPPORT_EMAIL}
            </a>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ----------------------------- 7. Final CTA ------------------------------- */

function FinalCta() {
  return (
    <section className="px-4 pb-24 sm:px-6">
      <Reveal>
        <div className="mx-auto max-w-6xl rounded-[2rem] bg-[#A3E635] px-6 py-16 text-center sm:px-12 md:py-20">
          <h2 className="mx-auto max-w-2xl text-3xl font-semibold tracking-tight text-[#0B0F19] sm:text-4xl">
            Your Hustle Deserves a Credit Score
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-[#0B0F19]/80">
            Start logging sales today and build the track record that lenders and suppliers can see.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/signup" className={inkBtn}>
              Get Started
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href="/login"
              className={`rounded-md text-sm font-semibold text-[#0B0F19] underline-offset-4 hover:underline ${focusRing}`}
            >
              I Already Have an Account
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ------------------------------- 8. Footer -------------------------------- */

type FooterLink = { label: string; href: string; external?: boolean };

const footerColumns: { title: string; links: FooterLink[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Features", href: "/#features" },
      { label: "How It Works", href: "/#how-it-works" },
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
      { label: "FAQ", href: "/#faq" },
    ],
  },
  {
    title: "Support",
    links: [
      { label: "WhatsApp", href: WHATSAPP_URL, external: true },
      { label: SUPPORT_EMAIL, href: `mailto:${SUPPORT_EMAIL}`, external: true },
    ],
  },
];

const legalLinks: FooterLink[] = [
  { label: "Privacy Policy", href: "/privacy" },
  { label: "Terms of Service", href: "/terms" },
];

const footerLinkClass = `rounded-md text-sm text-slate-600 transition hover:text-[#4d7c0f] hover:underline underline-offset-4 ${focusRing}`;

function FooterNavLink({ link }: { link: FooterLink }) {
  if (link.external) {
    return (
      <a href={link.href} target="_blank" rel="noopener noreferrer" className={footerLinkClass}>
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
    <footer className="border-t border-black/[0.07] bg-white">
      <div className="mx-auto max-w-6xl px-4 pb-8 pt-16 sm:px-6">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_2.8fr]">
          <div className="max-w-xs">
            <Link
              href="/"
              className={`rounded-md text-xl font-semibold tracking-tight text-[#0B0F19] ${focusRing}`}
            >
              Zaka<span className="text-[#4d7c0f]">Score</span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-slate-600">
              Private, on-device credit scoring for South African small businesses, traders, and hustlers.
            </p>
          </div>

          <nav aria-label="Footer" className="grid grid-cols-2 gap-8 sm:grid-cols-4">
            {footerColumns.map((col) => (
              <div key={col.title}>
                <h3 className="text-sm font-semibold text-[#0B0F19]">{col.title}</h3>
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

        <div className="mt-14 flex flex-col gap-4 border-t border-black/[0.07] pt-6 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© {new Date().getFullYear()} ZakaScore. All rights reserved.</p>
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
    <div className="min-h-screen overflow-x-clip bg-white font-sans text-[#0B0F19] antialiased">
      <Navbar />
      <main>
        <Hero />
        <TrustStrip />
        <Problem />
        <Solution />
        <Features />
        <HowItWorks />
        <Objections />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}