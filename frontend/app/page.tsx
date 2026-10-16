import Link from "next/link";
import type { ReactNode } from "react";
import {
  ArrowRight,
  BarChart3,
  Banknote,
  ChevronDown,
  EyeOff,
  FileQuestion,
  Mail,
  MessageCircle,
  Receipt,
  ShieldCheck,
  Smartphone,
  Users,
  WifiOff,
  type LucideIcon,
} from "lucide-react";
import { Navbar } from "@/components/navbar";
import { Reveal } from "@/components/reveal";

const WHATSAPP_URL = "https://wa.me/27735347153";
const SUPPORT_EMAIL = "support@zakascore.co.za";

// images
const IMAGES = {
  problem:
    "https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=1200&q=70",
  solution:
    "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1200&q=70",
};


// Constant Colors
const elevation =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.04),0_2px_4px_rgba(16,24,40,0.04),0_8px_16px_-4px_rgba(16,24,40,0.06),0_28px_56px_-18px_rgba(16,24,40,0.14)]";
const elevationSm =
  "shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_1px_1px_rgba(16,24,40,0.05),0_4px_10px_-2px_rgba(16,24,40,0.07)]";
const glass = `border border-black/[0.07] bg-gradient-to-b from-white/90 to-white/60 backdrop-blur-xl backdrop-saturate-150 ${elevation}`;
const glassInner = `border border-black/[0.06] bg-gradient-to-b from-white/90 to-white/60 backdrop-blur-md ${elevationSm}`;
const iconTile = `flex shrink-0 items-center justify-center rounded-xl border border-[#65a30d]/20 bg-[#f7fee7] text-[#4d7c0f] ${elevationSm}`;
const focusRing =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#4d7c0f]";

// mobile wider frames
const gutter = "px-[clamp(1.5rem,7vw,2rem)]";
const sectionY = "py-[clamp(3.5rem,14vw,5rem)] md:py-24";

const primaryBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-[#65a30d]/50 bg-gradient-to-b from-[#bef264] to-[#A3E635] px-6 py-3 text-sm font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_2px_rgba(16,24,40,0.12)] transition hover:brightness-105 active:brightness-95 ${focusRing}`;
const outlineBtn = `inline-flex items-center justify-center gap-2 rounded-xl border border-black/10 bg-gradient-to-b from-white to-white/60 px-6 py-3 text-sm font-semibold text-[#0B0F19] ${elevationSm} transition hover:border-[#65a30d]/50 hover:text-[#4d7c0f] ${focusRing}`;
const inkBtn = `inline-flex items-center justify-center gap-2 rounded-xl bg-[#0B0F19] px-6 py-3 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(16,24,40,0.2)] transition hover:bg-[#1f2937] ${focusRing}`;


//Layout Helpers
type Tone = "white" | "soft" | "lime";

const toneClass: Record<Tone, string> = {
  white: "bg-white",
  soft: "bg-slate-50",
  lime: "bg-[#f7fee7]",
};

//Separate Sections Nicely
function Section({
  id,
  tone = "white",
  children,
}: {
  id?: string;
  tone?: Tone;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      className={`relative flex min-h-[90svh] scroll-mt-16 items-center border-t border-black/[0.06] md:min-h-0 ${toneClass[tone]}`}
    >
      <div className={`mx-auto w-full max-w-6xl ${gutter} ${sectionY}`}>{children}</div>
    </section>
  );
}

function SectionHeading({
  eyebrow,
  title,
  text,
}: {
  eyebrow?: string;
  title: string;
  text?: string;
}) {
  return (
    <div className="max-w-2xl text-left">
      {eyebrow && (
        <p className="mb-4 flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.14em] text-[#4d7c0f]">
          <span aria-hidden="true" className="h-px w-8 bg-[#65a30d]/60" />
          {eyebrow}
        </p>
      )}
      <h2 className="text-[clamp(1.75rem,7vw,2rem)] font-semibold leading-[1.15] tracking-tight text-[#0B0F19] sm:text-4xl">
        {title}
      </h2>
      {text && <p className="mt-4 text-[clamp(0.9375rem,4vw,1rem)] leading-relaxed text-slate-600">{text}</p>}
    </div>
  );
}

function Photo({
  src,
  label,
  className = "",
  children,
}: {
  src: string;
  label: string;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <div
      role="img"
      aria-label={label}
      className={`relative isolate overflow-hidden rounded-2xl border border-black/[0.07] bg-gradient-to-br from-[#ecfccb] to-[#f7fee7] ${className}`}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt=""
        loading="lazy"
        decoding="async"
        className="absolute inset-0 h-full w-full object-cover"
      />
      {children}
    </div>
  );
}

// Flat dropdown row
function AccordionItem({
  icon: Icon,
  title,
  children,
}: {
  icon?: LucideIcon;
  title: string;
  children: ReactNode;
}) {
  return (
    <details className="group border-b border-black/[0.08]">
      <summary
        className={`flex cursor-pointer list-none items-center gap-4 py-5 text-left [&::-webkit-details-marker]:hidden ${focusRing}`}
      >
        {Icon && (
          <span className={`h-9 w-9 ${iconTile}`}>
            <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
          </span>
        )}
        <span className="flex-1 text-base font-semibold text-[#0B0F19]">{title}</span>
        <ChevronDown
          className="h-5 w-5 shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180 group-open:text-[#4d7c0f]"
          aria-hidden="true"
        />
      </summary>
      <p className={`pb-5 text-sm leading-relaxed text-slate-600 ${Icon ? "pl-[3.25rem]" : ""} pr-9`}>{children}</p>
    </details>
  );
}

//Phone mockup

function ScoreGauge({ score = 712 }: { score?: number }) {
  const pct = (score - 300) / 550;
  const arc = 126;
  return (
    <div className="relative mx-auto aspect-[12/7] w-full max-w-48">
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
      className="relative mx-auto w-full max-w-[17.5rem] sm:max-w-[18.75rem]"
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

//Hero
function Hero() {
  return (
    <section className="relative bg-gradient-to-bl from-[#a3e635] via-[#d9f99d] to-[#f7fee7]">
      <div
        className={`mx-auto grid min-h-[100svh] max-w-6xl items-center gap-[clamp(1.5rem,6vw,2.5rem)] ${gutter} pb-12 pt-28 text-center md:min-h-0 md:pb-16 md:pt-32 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] lg:gap-12 lg:pb-20 lg:pt-36 lg:text-left`}
      >
        <div className="motion-safe:animate-[rise_0.7s_cubic-bezier(0.22,0.61,0.36,1)_both]">
          <h1 className="text-balance text-[clamp(2rem,9vw,2.5rem)] leading-[1.1] tracking-tight text-[#0B0F19] sm:text-[clamp(2.25rem,5.5vw,3rem)] lg:text-[clamp(2.5rem,3.8vw,3.5rem)]">
            Turn Your Sales Into Financial Intelligence and Credit Potential
          </h1>
          <p className="mx-auto mt-[clamp(1.25rem,5vw,1.5rem)] max-w-xl text-[clamp(1rem,4vw,1.0625rem)] leading-relaxed text-slate-600 lg:mx-0">
            Track every sale, understand your business performance, and build an alternative credit score all in one simple app. Get financial intelligence from your daily transactions, discover your top-performing offerings, monitor revenue trends, and build a clearer picture of your business's financial activity.
          </p>
          <div className="mt-[clamp(1.75rem,7vw,2.25rem)] flex flex-row items-center justify-center gap-2.5 sm:gap-3 lg:justify-start">
            <Link
              href="/signup"
              className={`inline-flex items-center justify-center gap-2 rounded-xl bg-[#CC5500] !px-5 !py-2.5 text-[0.8125rem] font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.15),0_1px_2px_rgba(16,24,40,0.2)] transition hover:bg-[#3f6212] sm:!px-6 sm:!py-3 sm:text-sm ${focusRing}`}
            >
              Get Started
              <ArrowRight className="h-4 w-4 shrink-0" aria-hidden="true" />
            </Link>
            <Link
              href="/#how-it-works"
              className={`${outlineBtn} !px-5 !py-2.5 !text-[0.8125rem] sm:!px-6 sm:!py-3 sm:!text-sm`}
            >
              See How It Works
            </Link>
          </div>
        </div>

        {/* Hidden on phones; shown from md up */}
        <div className="relative mx-auto hidden w-full motion-safe:animate-[rise_0.8s_cubic-bezier(0.22,0.61,0.36,1)_0.15s_both] md:block">
          <PhoneMockup />
        </div>
      </div>
    </section>
  );
}

//Problem
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
    <Section tone="soft">
      <div className="grid gap-[clamp(2rem,8vw,3rem)] lg:grid-cols-2 lg:gap-x-16 lg:gap-y-10">
        <Reveal className="lg:col-start-1 lg:row-start-1">
          <SectionHeading
            title="Your Business Is Real. Your Paper Trail Isn’t."
            text="Plenty of South African businesses are doing well and still get turned away. Here’s why."
          />
        </Reveal>

        <Reveal delay={80} className="lg:col-start-2 lg:row-span-2 lg:row-start-1">
          <Photo
            src={IMAGES.problem}
            label="A small trader serving customers at a market stall"
            className="h-56 sm:h-64 lg:h-full lg:min-h-[28rem]"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F19]/55 via-transparent to-transparent" />
            <p className="absolute bottom-4 left-4 right-4 text-sm font-medium text-white">
              Real sales. No paperwork to prove them.
            </p>
          </Photo>
        </Reveal>

        <ol className="lg:col-start-1 lg:row-start-2">
          {problems.map(({ icon: Icon, title, text }, index) => (
            <Reveal
              as="li"
              key={title}
              delay={index * 100}
              className="flex gap-4 border-t border-black/[0.08] py-6 first:border-t-0 first:pt-0 last:pb-0"
            >
              <span className={`h-11 w-11 ${iconTile}`}>
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <div>
                <h3 className="text-lg font-semibold text-[#0B0F19]">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{text}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </div>
    </Section>
  );
}

//Solution

function CreditPassportCard() {
  const signals = [
    ["Revenue trend", "Growing"],
    ["Cash-flow consistency", "Steady"],
    ["Business activity", "Active"],
  ];
  return (
    <div className={`mx-auto w-full max-w-sm rounded-3xl p-[clamp(1.25rem,5vw,1.5rem)] ${glass}`}>
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

function LaptopMockup() {
  return (
    <div
      className="relative mx-auto w-full max-w-xl"
      role="img"
      aria-label="The ZakaScore dashboard shown on a laptop"
    >
      <div className="rounded-t-2xl border border-black/70 bg-[#0B0F19] px-[2.5%] pb-0 pt-[2.5%] shadow-[0_28px_56px_-18px_rgba(16,24,40,0.35)]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/dashboard-preview.png"
          alt=""
          loading="lazy"
          decoding="async"
          className="block aspect-[16/10] w-full rounded-t-md bg-white object-cover object-top"
        />
      </div>
      <div className="mx-auto -ml-[4%] h-3 w-[108%] rounded-b-2xl border border-black/10 bg-gradient-to-b from-slate-200 to-slate-400">
        <div className="mx-auto h-1 w-16 rounded-b-md bg-slate-400/80" />
      </div>
    </div>
  );
}

function Solution() {
  return (
    <Section id="solution" tone="white">
      <div className="grid items-center gap-[clamp(2.5rem,10vw,3.5rem)] lg:grid-cols-2 lg:gap-16">
        <Reveal delay={120} className="lg:order-2">
          <SectionHeading
            title="Turn Everyday Sales Into a Credit Profile That Speaks for You"
          />
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

        <Reveal className="lg:order-1">
          <LaptopMockup />
        </Reveal>
      </div>
    </Section>
  );
}

//How it works
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

function PhoneScreenshot() {
  const thickness = Array.from({ length: 12 });
  return (
    <div
      role="img"
      aria-label="The ZakaScore app showing a sale being logged"
      className="relative mx-auto flex aspect-square w-full max-w-sm items-center justify-center overflow-hidden rounded-3xl border border-black/[0.06] bg-gradient-to-bl from-[#bef264] via-[#d9f99d] to-[#f7fee7]"
    >
      <div className="absolute bottom-[8%] left-1/2 h-8 w-40 -translate-x-1/2 rounded-full bg-[#0B0F19]/25 blur-2xl" />

      <div className="[perspective:1300px]">
        <div className="relative aspect-[9/19.5] w-[7.5rem] [transform-style:preserve-3d] [transform:rotateX(14deg)_rotateY(26deg)_rotateZ(-16deg)] sm:w-[8.5rem]">
          {thickness.map((_, i) => (
            <div
              key={i}
              className="absolute inset-0 rounded-[2rem] bg-[#111827]"
              style={{ transform: `translateZ(-${(i + 1) * 1.5}px)` }}
            />
          ))}

          <div className="absolute inset-0 rounded-[2rem] border border-white/10 bg-[#0B0F19] p-[5px] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.12)]">
            <div className="relative h-full overflow-hidden rounded-[1.65rem] bg-white">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/logging-preview.png"
                alt=""
                loading="lazy"
                decoding="async"
                className="block h-full w-full object-cover object-top"
              />
              <div className="absolute left-1/2 top-2 h-3.5 w-14 -translate-x-1/2 rounded-full bg-[#0B0F19]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  return (
    <Section id="how-it-works" tone="lime">
      <div className="grid items-center gap-[clamp(2.5rem,10vw,3.5rem)] lg:grid-cols-2 lg:gap-16">
        <div>
          <Reveal>
            <SectionHeading  title="From Daily Sales to Credit Score in 3 Steps" />
          </Reveal>
          <ol className="mt-[clamp(2rem,8vw,2.5rem)] space-y-8">
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
          <PhoneScreenshot />
        </Reveal>
      </div>
    </Section>
  );
}

//FAQ
const objections: { title: string; text: string }[] = [
  {
    title: "What Is ZakaScore?",
    text: "ZakaScore turns your daily sales into an Alternative Credit Score. You record what you sell, it builds a picture of your revenue, consistency and growth, and you can take that score to suppliers and lenders instead of a payslip.",
  },
  {
    title: "Who Is It For?",
    text: "Small business owners who deal in cash and have no formal paper trail: traders, spaza shop owners, hairdressers, airtime sellers, stall holders and other hustlers.",
  },
  {
    title: "How Do I Log a Sale?",
    text: "Type it the way you would text a friend, for example “2 shirts, R300, cash”. ZakaScore reads it, shows you what it understood, and you confirm before anything is saved.",
  },
  {
    title: "What Happens If It Reads My Sale Wrong?",
    text: "Nothing gets recorded until you approve it. Every sale appears in a review screen first, so you can check the amount and payment type before you confirm.",
  },
  {
    title: "How Is My Score Calculated?",
    text: "Your score is built from your own logged sales: your revenue trend, how consistent your cash flow is, and how active your business is. The more regularly you log, the clearer the picture it can show.",
  },
  {
    title: "Is My Data Safe?",
    text: "The AI reads your messages on your own device, not on a cloud chatbot. Only the sale you confirm is saved to your account, and you review every sale before it is recorded.",
  },
  {
    title: "Do I Need Data or a New Phone?",
    text: "ZakaScore installs like an app and keeps working offline. The on-device assistant needs a recent browser with WebGPU. Without it, you can still type your sales and review them before saving.",
  },
  {
    title: "Can My Staff Use It Too?",
    text: "Yes. You can invite staff with one-time codes and keep every store in one place, so everyone's sales go into the same business record.",
  },
  {
    title: "Will Lenders Take It Seriously?",
    text: "Your score comes from real sales history, so you can show a track record instead of a promise. Every lender decides for itself, so treat it as strong supporting evidence, not a guarantee.",
  },
  {
    title: "What If Something Goes Wrong?",
    text: "Message us on WhatsApp or email support@zakascore.co.za. If something misbehaves while you are signed in, you can also open a ticket from your dashboard.",
  },
];

function Faq() {
  return (
    <Section id="faq" tone="white">
      <div className="max-w-3xl">
        <Reveal>
          <SectionHeading  title="Questions You Might Have" />
        </Reveal>
        <Reveal delay={80} className="mt-[clamp(2rem,8vw,2.5rem)] border-t border-black/[0.08]">
          {objections.map(({ title, text }) => (
            <AccordionItem key={title} title={title}>
              {text}
            </AccordionItem>
          ))}
        </Reveal>

        <Reveal className="mt-[clamp(3rem,12vw,4rem)]">
  <p className="font-semibold text-[#0B0F19]">Still unsure? Talk to a real person.</p>
  <p className="mt-1 text-sm leading-relaxed text-slate-600">
    Chat with us on WhatsApp, or open a ticket from inside your dashboard if something misbehaves.
  </p>
  <div className="mt-5 flex max-w-md flex-row gap-2.5 sm:gap-3">
    <a
      href={WHATSAPP_URL}
      target="_blank"
      rel="noopener noreferrer"
      className={`${outlineBtn} min-w-0 flex-1 !px-3 !py-2.5 !text-[clamp(0.8125rem,3.6vw,0.875rem)] sm:flex-none sm:!px-6 sm:!py-3`}
    >
      <MessageCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
      WhatsApp
    </a>
    <a
      href={`mailto:${SUPPORT_EMAIL}`}
      className={`${outlineBtn} min-w-0 flex-1 !px-3 !py-2.5 !text-[clamp(0.8125rem,3.6vw,0.875rem)] sm:flex-none sm:!px-6 sm:!py-3`}
    >
      <Mail className="h-4 w-4 shrink-0" aria-hidden="true" />
      Email Us
    </a>
  </div>
</Reveal>
      </div>
    </Section>
  );
}

//Final CTA
function FinalCta() {
  return (
    <section className="border-t border-black/[0.06] bg-white px-3 py-[clamp(1.5rem,6vw,2.5rem)] sm:px-6 md:py-16">
      <Reveal className="mx-auto w-full max-w-7xl">
        <div className="rounded-[2rem] bg-[#A3E635] px-[clamp(1.25rem,6vw,1.5rem)] py-[clamp(2.5rem,10vw,3.5rem)] text-center sm:px-12 md:py-20">
          <h2 className="mx-auto max-w-2xl text-[clamp(1.5rem,6vw,1.875rem)] font-semibold tracking-tight text-[#0B0F19] sm:text-4xl">
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
//Footer
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

const footerLinkClass = `rounded-md text-sm text-white/70 transition hover:text-[#A3E635] hover:underline underline-offset-4 ${focusRing}`;

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
    <footer className="border-t border-white/10 bg-[#0B0F19]">
      <div className={`mx-auto max-w-6xl ${gutter} pb-[clamp(2rem,8vw,2.5rem)] pt-[clamp(3rem,10vw,4rem)] md:pb-8`}>
        <div className="grid gap-[clamp(2rem,8vw,3rem)] lg:grid-cols-[1.2fr_2.8fr]">
          <div className="max-w-xs">
            <Link
              href="/"
              className="rounded-md text-xl font-semibold tracking-tight text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#A3E635]"
            >
              Zaka<span className="text-[#A3E635]">Score</span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-white/70">
              Private, on-device credit scoring for South African small businesses, traders, and hustlers.
            </p>
          </div>

          <nav aria-label="Footer" className="grid grid-cols-2 gap-[clamp(1.5rem,6vw,2rem)] sm:grid-cols-4">
            {footerColumns.map((col) => (
              <div key={col.title}>
                <h3 className="text-sm font-semibold text-white">{col.title}</h3>
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

        <div className="mt-[clamp(2.5rem,10vw,3.5rem)] flex flex-col gap-4 border-t border-white/10 pt-6 text-sm text-white/50 sm:flex-row sm:items-center sm:justify-between">
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

//Page
export default function Home() {
  return (
    <div className="landing min-h-screen overflow-x-clip bg-white font-sans text-[#0B0F19] antialiased">
      <Navbar />
      <main>
        <Hero />
        <Problem />
        <Solution />
        <HowItWorks />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}