import React from 'react';
import { Phone, Mail, ExternalLink, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-slate-800/80 bg-slate-950/90 backdrop-blur-xl mt-16 text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-blue-600 to-sky-400 flex items-center justify-center font-bold text-white text-xs shadow-md">
                FF
              </div>
              <span className="font-semibold text-slate-200 tracking-wide">FixFlow · Galaxy Care</span>
            </div>
            <p className="text-slate-400 text-[11px] leading-relaxed">
              Intelligent guided troubleshooting and self-care assistant for Samsung Galaxy smartphones, tablets, and One UI ecosystem devices.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Official Samsung Quality Standards</span>
            </div>
          </div>

          {/* Supported Topics */}
          <div className="space-y-2">
            <h4 className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
              Care Categories
            </h4>
            <ul className="space-y-1.5 text-[11px]">
              <li className="hover:text-slate-200 transition-colors">
                <span>Display &amp; Screen Diagnostics</span>
              </li>
              <li className="hover:text-slate-200 transition-colors">
                <span>Battery &amp; Device Care</span>
              </li>
              <li className="hover:text-slate-200 transition-colors">
                <span>Storage &amp; Memory Optimization</span>
              </li>
              <li className="hover:text-slate-200 transition-colors">
                <span>Accounts &amp; Cloud Backup</span>
              </li>
            </ul>
          </div>

          {/* Contact & Support (Rules 15 & 17) */}
          <div className="space-y-2">
            <h4 className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
              Customer Support
            </h4>
            <ul className="space-y-2 text-[11px]">
              <li>
                <a
                  href="tel:1-800-726-7864"
                  className="inline-flex items-center gap-2 text-slate-300 hover:text-sky-400 transition-colors font-mono"
                  title="Click to dial Samsung Customer Support"
                >
                  <Phone className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  <span>1-800-726-7864 (SAMSUNG)</span>
                </a>
              </li>
              <li>
                <a
                  href="mailto:support@fixflow.prism.samsung.com"
                  className="inline-flex items-center gap-2 text-slate-300 hover:text-sky-400 transition-colors font-mono"
                  title="Click to send email to FixFlow Support"
                >
                  <Mail className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span>support@fixflow.prism.samsung.com</span>
                </a>
              </li>
              <li className="text-[10px] text-slate-500">
                Toll-free 24/7 dedicated Galaxy hardware &amp; software support line.
              </li>
            </ul>
          </div>

          {/* Resources & Support */}
          <div className="space-y-2">
            <h4 className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
              Galaxy Care
            </h4>
            <ul className="space-y-1.5 text-[11px]">
              <li>
                <a
                  href="#support"
                  onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="inline-flex items-center gap-1.5 text-slate-300 hover:text-sky-400 transition-colors"
                >
                  <span>Samsung Care+ Coverage</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="#guide"
                  onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="inline-flex items-center gap-1.5 text-slate-300 hover:text-sky-400 transition-colors"
                >
                  <span>One UI 6.1 User Manual</span>
                </a>
              </li>
              <li>
                <a
                  href="#service"
                  onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="inline-flex items-center gap-1.5 text-slate-300 hover:text-sky-400 transition-colors"
                >
                  <span>Find a Samsung Service Center</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Copyright (Rule 16) */}
        <div className="pt-8 mt-8 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
          <p>© {currentYear} Samsung Electronics Co., Ltd. FixFlow Galaxy Smart Care. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">
              Galaxy AI Powered
            </span>
            <a
              href="#privacy"
              onClick={(e) => {
                e.preventDefault();
                alert('Privacy Guarantee: All diagnostic operations are processed with on-device safety. No personal data or files leave your device.');
              }}
              className="hover:text-slate-300 transition-colors"
            >
              Privacy Policy
            </a>
            <a
              href="#terms"
              onClick={(e) => {
                e.preventDefault();
                alert('FixFlow is an open-source research and hackathon prototype for Samsung smart device troubleshooting.');
              }}
              className="hover:text-slate-300 transition-colors"
            >
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
