import React, { useState } from 'react';
import { Navigation } from '../components/Navigation';

export default function LandingPage() {
  const [activeSection, setActiveSection] = useState('hero');

  const handleNavigate = (section) => {
    setActiveSection(section);
    // Scroll or navigate to the appropriate section.
    const sectionElement = document.getElementById(section);
    if (sectionElement) {
      sectionElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div>
      {/* Navigation now imported */}
      <Navigation activeSection={activeSection} onNavigate={handleNavigate} />

      {/* Landing page sections */}
      <section id="hero">Home Section</section>
      <section id="problem">The Problem Section</section>
      <section id="philosophy">Our Philosophy Section</section>
      <section id="features">Features Section</section>
      <section id="how-it-works">How It Works Section</section>
      <section id="safety">Safety Section</section>
      <section id="pricing">Pricing Section</section>
      <section id="support">Support Section</section>
      <section id="cta">Get Started Section</section>
    </div>
  );
}