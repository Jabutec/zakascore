"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import type { InputHTMLAttributes, ReactNode } from "react";
import { ChevronDown, Eye, EyeOff } from "lucide-react";

// Same logo file used in the workspace and dashboard (lives in frontend/public).
const LOGO_SRC = "/logo.png";

/* -------------------------------------------------------------------------- */
/*  Shared look: white surfaces, glossy lime buttons, hairline borders.       */
/*  Radius system: 12px controls (rounded-xl), 16px panels (rounded-2xl).     */
/* -------------------------------------------------------------------------- */

/* text-base on phones stops iOS zooming into the field on focus (a cause of "shaking") */
const inputClass =
  "h-11 w-full rounded-xl border border-black/10 bg-white px-4 text-base text-[#0B0F19] outline-none transition placeholder:text-slate-400 focus:border-[#65a30d]/60 focus:shadow-[0_0_0_2px_rgba(163,230,53,0.45)] disabled:opacity-60 sm:text-sm";

export const limeButton =
  "relative isolate flex h-11 w-full items-center justify-center overflow-hidden rounded-xl border border-[#65a30d]/50 bg-gradient-to-b from-[#bef264] to-[#A3E635] px-5 text-sm font-semibold text-[#0B0F19] shadow-[inset_0_1px_0_rgba(255,255,255,0.6),0_1px_2px_rgba(16,24,40,0.12)] transition before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:-z-10 before:h-1/2 before:bg-gradient-to-b before:from-white/40 before:to-transparent hover:brightness-105 active:brightness-95 disabled:cursor-not-allowed disabled:opacity-50";

export const textLink = "font-medium text-[#4d7c0f] underline-offset-4 hover:underline";

/* ------------------------------ Form pieces ------------------------------- */

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
};

export function Field({ label, hint, className = "", ...inputProps }: FieldProps) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-[#0B0F19]">{label}</span>
      <input {...inputProps} className={`${inputClass} mt-1.5 ${className}`} />
      {hint && <span className="mt-1.5 block text-xs leading-relaxed text-slate-500">{hint}</span>}
    </label>
  );
}

/* Password input with a show/hide toggle that works on every device
   (the browser's built-in eye only exists on some desktop browsers). */
export function PasswordField({
  label,
  hint,
  className = "",
  ...inputProps
}: Omit<FieldProps, "type">) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="block">
      <span className="text-sm font-medium text-[#0B0F19]">{label}</span>
      <div className="relative mt-1.5">
        <input
          {...inputProps}
          type={visible ? "text" : "password"}
          className={`${inputClass} pr-12 [&::-ms-reveal]:hidden ${className}`}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-xl text-slate-500 transition hover:text-[#4d7c0f] focus-visible:text-[#4d7c0f] focus-visible:outline-none"
        >
          {visible ? (
            <EyeOff className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Eye className="h-5 w-5" aria-hidden="true" />
          )}
        </button>
      </div>
      {hint && <span className="mt-1.5 block text-xs leading-relaxed text-slate-500">{hint}</span>}
    </label>
  );
}

export function CheckboxField({
  name,
  required,
  children,
}: {
  name: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 text-sm leading-relaxed text-slate-600">
      <input
        type="checkbox"
        name={name}
        required={required}
        className="mt-0.5 h-5 w-5 shrink-0 cursor-pointer rounded-md accent-[#65a30d]"
      />
      <span>{children}</span>
    </label>
  );
}

export function FormAlert({ children }: { children: ReactNode }) {
  return (
    <p
      role="alert"
      className="mb-5 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm leading-relaxed text-red-700"
    >
      {children}
    </p>
  );
}

/* Optional invite code: collapsed by default so the common case stays uncluttered. */
export function ConnectCodeField({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <details className="group rounded-xl border border-black/10 bg-white px-4 py-3">
      <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-[#0B0F19] [&::-webkit-details-marker]:hidden">
        Have a Connect Code?
        <ChevronDown
          className="h-4 w-4 text-slate-400 transition group-open:rotate-180"
          aria-hidden="true"
        />
      </summary>
      <div className="mt-3">
        <Field
          label="Connect Code (Optional)"
          hint="Joining an existing business? Enter the one-time code your team gave you."
          value={value}
          onChange={(event) => onChange(event.target.value.toUpperCase())}
          autoComplete="off"
          maxLength={32}
          className="uppercase tracking-widest"
        />
      </div>
    </details>
  );
}

/* ------------------------------ Split screen ------------------------------ */
/*  Phones: full-bleed page, no rounded sheet, no backdrop, no nested scroll.     */
/*  lg and up: a rounded "sheet" floating on a soft grey backdrop, with a lime    */
/*  panel on one side and the form on the other.                                  */

export function AuthShell({
  title,
  subtitle,
  footer,
  children,
  heading = "Get Started",
  panel = "left",
}: {
  title: string;
  subtitle?: string;
  footer?: ReactNode;
  children: ReactNode;
  /** Text on the lime panel */
  heading?: string;
  /** Which side the lime panel sits on (the form takes the other side) */
  panel?: "left" | "right";
}) {
  const panelOnLeft = panel === "left";

  return (
    <main className="flex min-h-svh items-center justify-center overflow-x-clip bg-white text-[#0B0F19] lg:min-h-dvh lg:bg-[#f2f4f7] lg:p-6">
      <div className="grid min-h-svh w-full max-w-5xl grid-rows-[auto_1fr] bg-white lg:h-[min(700px,calc(100dvh-3rem))] lg:min-h-0 lg:grid-cols-2 lg:grid-rows-1 lg:overflow-hidden lg:rounded-[2rem] lg:border lg:border-black/[0.06] lg:shadow-[0_1px_2px_rgba(16,24,40,0.06),0_24px_64px_-24px_rgba(16,24,40,0.2)]">
        {/* Thin lime strip on phones, where the full lime panel is hidden */}
        <div aria-hidden="true" className="h-2 bg-[#A3E635] lg:hidden" />

        <section className="flex min-h-0 flex-col px-6 pb-[max(2.5rem,env(safe-area-inset-bottom))] pt-10 sm:px-12 lg:overflow-y-auto lg:px-14 lg:py-10">
          <div className="mx-auto my-auto w-full max-w-sm">
            <Link href="/" className="inline-flex items-center gap-3 rounded-xl" aria-label="ZakaScore home">
              <span className="relative inline-flex h-10 w-10 shrink-0 overflow-hidden rounded-xl border border-black/[0.07] bg-white shadow-[0_1px_2px_rgba(16,24,40,0.06)]">
                <Image
                  src={LOGO_SRC}
                  alt=""
                  fill
                  sizes="40px"
                  className="scale-[1.45] object-cover"
                  priority
                />
              </span>
              <span className="text-[17px] font-semibold tracking-tight">
                Zaka<span className="text-[#4d7c0f]">Score</span>
              </span>
            </Link>

            <h1 className="mt-8 text-[28px] font-semibold leading-tight tracking-tight">{title}</h1>
            {subtitle && <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{subtitle}</p>}

            <div className="mt-6">{children}</div>

            {footer && <div className="mt-6 text-center text-sm text-slate-600">{footer}</div>}
          </div>
        </section>

        {/* Plain lime panel. Rounded only on the side facing the form. */}
        <aside
          aria-hidden="true"
          className={`hidden flex-col justify-end bg-[#A3E635] p-12 lg:flex ${
            panelOnLeft ? "lg:order-first lg:rounded-r-3xl" : "lg:order-last lg:rounded-l-3xl"
          }`}
        >
          <p className="text-5xl font-semibold leading-[1.05] tracking-tight text-[#0B0F19] xl:text-6xl">
            {heading}
          </p>
        </aside>
      </div>
    </main>
  );
}