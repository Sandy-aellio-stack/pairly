import { useState } from 'react';

const navItems = [
  { id: 'hero', label: 'Home' },
  { id: 'problem', label: 'The Problem' },
  { id: 'philosophy', label: 'Our Philosophy' },
  { id: 'features', label: 'Features' },
  { id: 'how-it-works', label: 'How It Works' },
  { id: 'safety', label: 'Safety' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'support', label: 'Support' },
  { id: 'cta', label: 'Get Started' },
];

export function Navigation({ activeSection, onNavigate }) {
  return (
    <nav className="fixed left-8 top-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-6 hidden lg:flex">
      <div className="flex flex-col gap-6">
        {navItems.map((item) => {
          const isActive = activeSection === item.id;

          return (
            <div key={item.id} className="flex flex-col items-center">
              {/* Dot */}
              <button
                onClick={() => onNavigate(item.id)}
                aria-label={item.label}
                className={`w-3 h-3 rounded-full border-2 transition-all duration-300 ${
                  isActive
                    ? 'bg-[#3390FF] border-[#3390FF] scale-125'
                    : 'bg-transparent border-[#3390FF]/60 hover:border-[#3390FF] hover:scale-110'
                }`}
              />

              {/* Active section label BELOW dot */}
              {isActive && (
                <span className="mt-2 text-xs text-[#3390FF] font-medium tracking-wide whitespace-nowrap transition-opacity duration-300">
                  {item.label}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </nav>
  );
}

export default Navigation;
