import { useState } from 'react';
import { Coins, Check, Info } from 'lucide-react';

const pricingTiers = [
  {
    name: 'Starter',
    coins: 100,
    price: 9.99,
    features: [
      '100 conversation coins',
      'Basic matching',
      'Profile verification',
      'Standard support',
    ],
  },
  {
    name: 'Popular',
    coins: 300,
    price: 24.99,
    features: [
      '300 conversation coins',
      'Priority matching',
      'Advanced filters',
      'Profile boost',
      'Priority support',
    ],
    popular: true,
  },
  {
    name: 'Premium',
    coins: 600,
    price: 44.99,
    features: [
      '600 conversation coins',
      'Unlimited matching',
      'All advanced features',
      'Monthly profile boost',
      'VIP support',
      'Read receipts',
    ],
  },
];

const PricingSection = ({ onGetStarted }) => {
  const [selectedTier, setSelectedTier] = useState(1);

  return (
    <section id="pricing" className="py-28 bg-white lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-sm font-semibold text-[#0F172A] uppercase tracking-wider">💰 Pricing</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            Transparent & Fair Pricing
          </h2>
          <p className="text-xl text-gray-600">
            TrueBond uses a transparent and fair pricing model. One coin = one message.
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto mb-12">
          {pricingTiers.map((tier, index) => (
            <button
              key={index}
              onClick={() => setSelectedTier(index)}
              className={`rounded-2xl p-8 transition-all text-left ${
                tier.popular
                  ? 'bg-[#0F172A] text-white shadow-2xl scale-105 relative'
                  : selectedTier === index
                  ? 'bg-white border-2 border-[#0F172A] shadow-xl'
                  : 'bg-white border-2 border-gray-200 hover:border-[#0F172A] hover:shadow-lg'
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#FCE7F3] text-[#0F172A] text-xs font-bold px-3 py-1 rounded-full">
                  MOST POPULAR
                </div>
              )}
              <h3 className={`text-2xl font-bold mb-2 ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>{tier.name}</h3>
              <div className="mb-6">
                <span className={`text-4xl font-bold ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>
                  ${tier.price}
                </span>
                <span className={tier.popular ? 'text-white/70' : 'text-gray-500'}> / {tier.coins} coins</span>
              </div>
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <Check size={18} className={tier.popular ? 'text-white mr-2 flex-shrink-0' : 'text-green-500 mr-2 flex-shrink-0'} />
                    <span className={`text-sm ${tier.popular ? 'text-white/90' : 'text-gray-600'}`}>{feature}</span>
                  </li>
                ))}
              </ul>
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  onGetStarted && onGetStarted();
                }}
                className={`w-full py-3 rounded-xl font-semibold text-center transition-all cursor-pointer ${
                  tier.popular
                    ? 'bg-white text-[#0F172A] hover:bg-gray-100'
                    : 'bg-[#0F172A] text-white hover:shadow-lg'
                }`}
              >
                Get Started
              </div>
            </button>
          ))}
        </div>
        
        <div className="max-w-3xl mx-auto bg-[#E9D5FF]/30 rounded-2xl p-8 border-2 border-[#E9D5FF]">
          <div className="flex items-start space-x-4">
            <Info size={24} className="text-[#0F172A] flex-shrink-0" />
            <div>
              <h4 className="text-lg font-semibold text-[#0F172A] mb-2">Why This Model?</h4>
              <p className="text-gray-600 mb-4">
                It encourages thoughtful communication instead of spam. Every message is intentional, meaningful, and valued.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <Check size={16} className="text-green-600 mr-2" />
                  No hidden charges
                </li>
                <li className="flex items-center">
                  <Check size={16} className="text-green-600 mr-2" />
                  No forced subscriptions
                </li>
                <li className="flex items-center">
                  <Check size={16} className="text-green-600 mr-2" />
                  You only pay when you choose to engage
                </li>
                <li className="flex items-center">
                  <Check size={16} className="text-green-600 mr-2" />
                  Minimum top-up starts at 100 coins
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
