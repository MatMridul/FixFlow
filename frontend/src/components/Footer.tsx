import React from 'react';
import { Phone, Mail, ExternalLink, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t border-white/[0.07] bg-[#0E1013] mt-16 text-zinc-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Brand */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 rounded bg-[#1E56FF] flex items-center justify-center font-bold text-white text-[10px]">
                FF
              </div>
              <span className="font-semibold text-zinc-200">FixFlow Galaxy Care</span>
            </div>
            <p className="text-zinc-400 text-[11px] leading-relaxed">
              Intelligent guided troubleshooting assistant for Samsung Galaxy smartphones and One UI ecosystem devices.
            </p>
            <div className="flex items-center gap-1.5 text-[11px] text-emerald-400">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Samsung Care Standards</span>
            </div>
          </div>

          {/* Categories */}
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">
              Diagnostic Categories
            </h4>
            <ul className="space-y-1 text-[11px]">
              <li className="hover:text-zinc-200 transition-colors">Display &amp; Screen Diagnostics</li>
              <li className="hover:text-zinc-200 transition-colors">Battery &amp; Device Care</li>
              <li className="hover:text-zinc-200 transition-colors">Storage &amp; Memory Optimization</li>
              <li className="hover:text-zinc-200 transition-colors">System Stability &amp; Safe Mode</li>
            </ul>
          </div>

          {/* Support (Rules 15 & 17) */}
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">
              Customer Support
            </h4>
            <ul className="space-y-1.5 text-[11px]">
              <li>
                <a
                  href="tel:1-800-726-7864"
                  className="inline-flex items-center gap-1.5 text-zinc-300 hover:text-white transition-colors font-mono"
                  title="Click to dial Samsung Customer Support"
                >
                  <Phone className="w-3.5 h-3.5 text-[#1E56FF] shrink-0" />
                  <span>1-800-726-7864</span>
                </a>
              </li>
              <li>
                <a
                  href="mailto:support@fixflow.prism.samsung.com"
                  className="inline-flex items-center gap-1.5 text-zinc-300 hover:text-white transition-colors font-mono"
                  title="Click to send email to FixFlow Support"
                >
                  <Mail className="w-3.5 h-3.5 text-[#1E56FF] shrink-0" />
                  <span>support@fixflow.prism.samsung.com</span>
                </a>
              </li>
              <li className="text-[10px] text-zinc-500">
                Toll-free 24/7 dedicated Galaxy hardware &amp; software support line.
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div className="space-y-1.5">
            <h4 className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">
              Galaxy Care
            </h4>
            <ul className="space-y-1 text-[11px]">
              <li>
                <a
                  href="#support"
                  onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="inline-flex items-center gap-1 text-zinc-300 hover:text-white transition-colors"
                >
                  <span>Samsung Care+ Coverage</span>
                  <ExternalLink className="w-3 h-3 text-zinc-500" />
                </a>
              </li>
              <li>
                <a
                  href="#guide"
                  onClick={(e) => {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="inline-flex items-center gap-1 text-zinc-300 hover:text-white transition-colors"
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
                  className="inline-flex items-center gap-1 text-zinc-300 hover:text-white transition-colors"
                >
                  <span>Find Service Center</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar: Copyright (Rule 16) */}
        <div className="pt-6 mt-6 border-t border-white/[0.05] flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-zinc-500">
          <p>© {currentYear} Samsung Electronics Co., Ltd. FixFlow Galaxy Smart Care. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="text-zinc-400">One UI 6.1 Verified</span>
            <a
              href="#privacy"
              onClick={(e) => {
                e.preventDefault();
                alert('Privacy Guarantee: All diagnostic operations are processed with on-device safety. No personal data or files leave your device.');
              }}
              className="hover:text-zinc-300 transition-colors"
            >
              Privacy Policy
            </a>
            <a
              href="#terms"
              onClick={(e) => {
                e.preventDefault();
                alert('FixFlow is an open-source prototype for Samsung smart device troubleshooting.');
              }}
              className="hover:text-zinc-300 transition-colors"
            >
              Terms of Service
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
