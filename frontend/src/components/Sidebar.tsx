"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  TrendingUp,
  Microscope,
  FlaskConical,
} from "lucide-react";

const NAV = [
  { href: "/", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/chat", icon: MessageSquare, label: "Chatbot" },
  { href: "/forecast", icon: TrendingUp, label: "Forecast" },
  { href: "/explain", icon: Microscope, label: "Explainability" },
  { href: "/whatif", icon: FlaskConical, label: "What-if" },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside className="fixed top-0 left-0 h-screen w-56 bg-slate-900 border-r border-slate-800 flex flex-col z-50">
      {/* Logo */}
      <div className="px-3 py-5 border-b border-slate-800">
        <div className="px-3">
          <p className="text-base font-bold text-slate-100 leading-tight">
            Phuket Traffic
          </p>
          <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
            LLM Framework
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = path === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150
                ${
                  active
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800">
        <p className="text-[10px] text-slate-600 leading-relaxed">
          TFE — Mathieu Zilli
          <br />
          UMons × PSU Phuket
          <br />
          xTP-LLM · LoRA · SHAP
        </p>
      </div>
    </aside>
  );
}
