import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Shield, Eye, Lock, MapPin } from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const PrivacySection = () => {
  const sectionRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.privacy-item', {
        y: 60,
        opacity: 0,
        stagger: 0.15,
        duration: 0.8,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 70%',
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="section py-32 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/10 rounded-full border border-green-500/30 mb-8">
            <Shield size={16} className="text-green-400" />
            <span className="text-sm text-green-300">Privacy First</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6">
            Your <span className="gradient-text">Privacy Matters</span>
          </h2>
          <p className="text-xl text-white/60 max-w-2xl mx-auto">
            We take your security seriously. Here's how we protect you.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="privacy-item card-dark flex gap-6">
            <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-green-500/20 flex items-center justify-center">
              <Lock size={24} className="text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Address is Private</h3>
              <p className="text-white/60">
                Your address is stored securely and encrypted. It's only used for verification and compliance purposes.
              </p>
            </div>
          </div>

          <div className="privacy-item card-dark flex gap-6">
            <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-green-500/20 flex items-center justify-center">
              <Eye size={24} className="text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Never Shown Publicly</h3>
              <p className="text-white/60">
                Your address will never appear on your profile, in search results, or be visible to other users.
              </p>
            </div>
          </div>

          <div className="privacy-item card-dark flex gap-6">
            <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center">
              <MapPin size={24} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Location for Discovery</h3>
              <p className="text-white/60">
                Your live location is only used to show nearby users. We only share approximate distance, never exact location.
              </p>
            </div>
          </div>

          <div className="privacy-item card-dark flex gap-6">
            <div className="flex-shrink-0 w-14 h-14 rounded-2xl bg-purple-500/20 flex items-center justify-center">
              <Shield size={24} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">You're in Control</h3>
              <p className="text-white/60">
                You decide when to share your location. Turn it off anytime from your settings. Your data, your rules.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PrivacySection;
