import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Coins, MessageCircle, IndianRupee, Sparkles } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const CreditsSection = () => {
  const sectionRef = useRef(null);
  const counterRef = useRef(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Counter animation
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 60%',
        onEnter: () => {
          gsap.to({}, {
            duration: 2,
            ease: 'power2.out',
            onUpdate: function() {
              setCount(Math.floor(this.progress() * 10));
            },
          });
        },
      });

      // Cards animation
      gsap.from('.credit-card', {
        y: 80,
        opacity: 0,
        stagger: 0.2,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 60%',
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="section py-32 px-6 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-900/10 to-transparent" />

      <div className="max-w-7xl mx-auto relative z-10">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/10 rounded-full border border-purple-500/30 mb-8">
            <Coins size={16} className="text-purple-400" />
            <span className="text-sm text-purple-300">Credits System</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Simple & <span className="gradient-text">Transparent</span>
          </h2>
          <p className="text-xl text-white/60 max-w-2xl mx-auto">
            No hidden fees. No subscriptions. Just pay for what you use.
          </p>
        </div>

        {/* Animated counter */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center justify-center gap-4 px-12 py-8 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-3xl border border-purple-500/30">
            <Sparkles size={40} className="text-purple-400" />
            <div>
              <div ref={counterRef} className="text-7xl font-bold gradient-text">
                {count}
              </div>
              <div className="text-white/60">Free coins on signup</div>
            </div>
          </div>
        </div>

        {/* Info cards */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="credit-card card-dark text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mx-auto mb-6">
              <MessageCircle size={28} className="text-white" />
            </div>
            <h3 className="text-2xl font-bold mb-3">1 Coin = 1 Message</h3>
            <p className="text-white/60">
              Each message you send costs just 1 coin. Simple math, no surprises.
            </p>
          </div>

          <div className="credit-card card-dark text-center border-purple-500/30">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-pink-500 flex items-center justify-center mx-auto mb-6">
              <IndianRupee size={28} className="text-white" />
            </div>
            <h3 className="text-2xl font-bold mb-3">Starting ₹100</h3>
            <p className="text-white/60">
              Need more coins? Buy packs starting from just ₹100. No minimum commitment.
            </p>
          </div>

          <div className="credit-card card-dark text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-500 flex items-center justify-center mx-auto mb-6">
              <Coins size={28} className="text-white" />
            </div>
            <h3 className="text-2xl font-bold mb-3">No Expiry</h3>
            <p className="text-white/60">
              Your coins never expire. Use them whenever you're ready to connect.
            </p>
          </div>
        </div>

        {/* Credit packages preview */}
        <div className="mt-16 text-center">
          <h3 className="text-2xl font-bold mb-8">Available Packages</h3>
          <div className="flex flex-wrap justify-center gap-4">
            {[
              { price: 100, coins: 50 },
              { price: 250, coins: 150 },
              { price: 500, coins: 350 },
              { price: 1000, coins: 800 },
            ].map((pkg, i) => (
              <div
                key={i}
                className="px-6 py-4 bg-white/5 rounded-2xl border border-white/10 hover:border-purple-500/50 transition-colors"
              >
                <div className="text-2xl font-bold gradient-text">₹{pkg.price}</div>
                <div className="text-white/60 text-sm">{pkg.coins} coins</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default CreditsSection;
