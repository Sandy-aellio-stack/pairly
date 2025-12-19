import { useState } from 'react';
import { Coins, Check, Info, Sparkles, MessageCircle, Phone, Video } from 'lucide-react';

const pricingTiers = [
  {
    name: 'Starter',
    coins: 100,
    price: 100,
    pricePerCoin: 1,
    discount: 0,
    features: [
      '100 coins',
      '₹1 per coin',
      'Basic matching',
      'Profile verification',
    ],
  },
  {
    name: 'Popular',
    coins: 500,
    price: 450,
    pricePerCoin: 0.9,
    discount: 10,
    features: [
      '500 coins',
      '₹0.90 per coin (10% off)',
      'Priority matching',
      'Advanced filters',
      'Profile boost',
    ],
    popular: true,
  },
  {
    name: 'Premium',
    coins: 1000,
    price: 800,
    pricePerCoin: 0.8,
    discount: 20,
    features: [
      '1000 coins',
      '₹0.80 per coin (20% off)',
      'Unlimited matching',
      'All features included',
      'VIP support',
    ],
  },
];

const PricingSection = ({ onGetStarted }) => {
  const [selectedTier, setSelectedTier] = useState(1);

  return (
    <section id="pricing" className="py-28 bg-white lg:pl-20">
      <div className="container mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <span className="text-sm font-semibold text-[#7C3AED] uppercase tracking-wider">Pricing</span>
          <h2 className="text-4xl md:text-5xl font-bold text-[#0F172A] mt-4 mb-4">
            Simple, Fair Pricing
          </h2>
          <p className="text-xl text-gray-600 mb-6">
            Pay only for what you use. No subscriptions, no hidden fees.
          </p>
          
          {/* Coin Usage Explanation */}
          <div className="bg-[#E9D5FF]/30 rounded-2xl p-6 max-w-xl mx-auto">
            <h4 className="font-semibold text-[#0F172A] mb-4">How Coins Work</h4>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <MessageCircle size={24} className="mx-auto text-[#0F172A] mb-2" />
                <p className="font-bold text-[#0F172A]">1 coin</p>
                <p className="text-xs text-gray-500">per message</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <Phone size={24} className="mx-auto text-[#0F172A] mb-2" />
                <p className="font-bold text-[#0F172A]">5 coins</p>
                <p className="text-xs text-gray-500">per min (voice)</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <Video size={24} className="mx-auto text-[#0F172A] mb-2" />
                <p className="font-bold text-[#0F172A]">10 coins</p>
                <p className="text-xs text-gray-500">per min (video)</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-12">
          {pricingTiers.map((tier, index) => (
            <button
              key={index}
              onClick={() => setSelectedTier(index)}
              className={`rounded-2xl p-6 transition-all text-left relative ${
                tier.popular
                  ? 'bg-[#0F172A] text-white shadow-2xl scale-105'
                  : selectedTier === index
                  ? 'bg-white border-2 border-[#0F172A] shadow-xl'
                  : 'bg-white border-2 border-gray-200 hover:border-[#0F172A] hover:shadow-lg'
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#E9D5FF] text-[#0F172A] text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                  <Sparkles size={12} />
                  BEST VALUE
                </div>
              )}
              
              {tier.discount > 0 && (
                <div className={`inline-block px-2 py-1 rounded text-xs font-bold mb-2 ${
                  tier.popular ? 'bg-green-400 text-green-900' : 'bg-green-100 text-green-700'
                }`}>
                  {tier.discount}% OFF
                </div>
              )}
              
              <h3 className={`text-xl font-bold mb-2 ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>
                {tier.name}
              </h3>
              
              <div className="mb-2">
                <span className={`text-3xl font-bold ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>
                  ₹{tier.price}
                </span>
              </div>
              
              <p className={`text-sm mb-4 ${tier.popular ? 'text-white/70' : 'text-gray-500'}`}>
                {tier.coins} coins
              </p>
              
              <ul className="space-y-2 mb-6">
                {tier.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <Check size={16} className={tier.popular ? 'text-green-400 mr-2 flex-shrink-0 mt-0.5' : 'text-green-500 mr-2 flex-shrink-0 mt-0.5'} />
                    <span className={`text-sm ${tier.popular ? 'text-white/90' : 'text-gray-600'}`}>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  onGetStarted && onGetStarted();
                }}
                className={`w-full py-2.5 rounded-xl font-semibold text-center transition-all cursor-pointer ${
                  tier.popular
                    ? 'bg-white text-[#0F172A] hover:bg-gray-100'
                    : 'bg-[#0F172A] text-white hover:shadow-lg'
                }`}
              >
                Buy Now
              </div>
            </button>
          ))}
        </div>
        
        {/* Info Box */}
        <div className="max-w-3xl mx-auto bg-gray-50 rounded-2xl p-6 border border-gray-200">
          <div className="flex items-start space-x-4">
            <Info size={24} className="text-[#0F172A] flex-shrink-0" />
            <div>
              <h4 className="text-lg font-semibold text-[#0F172A] mb-2">Why Coins?</h4>
              <p className="text-gray-600 text-sm">
                Coins encourage thoughtful communication. When every message costs something, 
                people think before they type. This means fewer "hey" messages and more genuine conversations.
              </p>
              <div className="flex flex-wrap gap-4 mt-4 text-sm text-gray-600">
                <span className="flex items-center"><Check size={14} className="text-green-600 mr-1" /> Coins never expire</span>
                <span className="flex items-center"><Check size={14} className="text-green-600 mr-1" /> 10 free coins on signup</span>
                <span className="flex items-center"><Check size={14} className="text-green-600 mr-1" /> No subscriptions</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
