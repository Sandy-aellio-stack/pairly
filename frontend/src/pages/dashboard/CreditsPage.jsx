import { useState } from 'react';
import { Coins, Check, Sparkles, CreditCard, History, Gift } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const pricingTiers = [
  {
    name: 'Starter',
    coins: 100,
    price: 100,
    pricePerCoin: 1,
    discount: 0,
  },
  {
    name: 'Popular',
    coins: 500,
    price: 450,
    pricePerCoin: 0.9,
    discount: 10,
    popular: true,
  },
  {
    name: 'Premium',
    coins: 1000,
    price: 800,
    pricePerCoin: 0.8,
    discount: 20,
  },
];

const transactionHistory = [
  { id: 1, type: 'purchase', amount: 100, coins: 100, date: '2024-12-18', description: 'Starter Pack' },
  { id: 2, type: 'bonus', amount: 0, coins: 10, date: '2024-12-17', description: 'Welcome Bonus' },
  { id: 3, type: 'spent', amount: 0, coins: -5, date: '2024-12-16', description: 'Messages sent' },
];

const CreditsPage = () => {
  const { user } = useAuthStore();
  const [selectedTier, setSelectedTier] = useState(1);

  const handlePurchase = (tier) => {
    toast.success(`Processing purchase of ${tier.coins} coins for ₹${tier.price}`);
    // TODO: Implement Razorpay payment
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* Balance Card */}
      <div className="bg-gradient-to-r from-[#0F172A] to-[#1E293B] rounded-3xl p-8 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/70 text-sm mb-1">Your Balance</p>
            <div className="flex items-center gap-3">
              <Coins size={40} className="text-yellow-400" />
              <span className="text-5xl font-bold">{user?.credits_balance || 10}</span>
              <span className="text-white/70">coins</span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white/70 text-sm">1 coin = 1 message</p>
            <p className="text-white/70 text-sm">₹1 = 1 coin</p>
          </div>
        </div>
      </div>

      {/* Buy Coins */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-[#0F172A] mb-6">Buy Coins</h2>
        
        <div className="grid md:grid-cols-3 gap-4">
          {pricingTiers.map((tier, index) => (
            <button
              key={index}
              onClick={() => setSelectedTier(index)}
              className={`rounded-2xl p-6 transition-all text-left relative ${
                tier.popular
                  ? 'bg-[#0F172A] text-white shadow-2xl scale-105'
                  : selectedTier === index
                  ? 'bg-white border-2 border-[#0F172A] shadow-xl'
                  : 'bg-white border-2 border-gray-200 hover:border-[#0F172A]'
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#FCE7F3] text-[#0F172A] text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                  <Sparkles size={12} />
                  BEST VALUE
                </div>
              )}
              
              {tier.discount > 0 && (
                <span className={`inline-block px-2 py-1 rounded text-xs font-bold mb-2 ${
                  tier.popular ? 'bg-green-400 text-green-900' : 'bg-green-100 text-green-700'
                }`}>
                  {tier.discount}% OFF
                </span>
              )}
              
              <h3 className={`text-lg font-bold mb-1 ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>
                {tier.name}
              </h3>
              
              <div className="flex items-baseline gap-1 mb-1">
                <Coins size={20} className={tier.popular ? 'text-yellow-400' : 'text-yellow-500'} />
                <span className={`text-3xl font-bold ${tier.popular ? 'text-white' : 'text-[#0F172A]'}`}>
                  {tier.coins}
                </span>
              </div>
              
              <p className={`text-sm mb-4 ${tier.popular ? 'text-white/70' : 'text-gray-500'}`}>
                ₹{tier.price} • ₹{tier.pricePerCoin.toFixed(2)}/coin
              </p>
              
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  handlePurchase(tier);
                }}
                className={`w-full py-2.5 rounded-xl font-semibold text-center transition-all cursor-pointer ${
                  tier.popular
                    ? 'bg-white text-[#0F172A] hover:bg-gray-100'
                    : 'bg-[#0F172A] text-white hover:bg-gray-800'
                }`}
              >
                Buy Now
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* How Coins Work */}
      <div className="bg-[#E9D5FF]/30 rounded-2xl p-6 mb-8">
        <h3 className="font-semibold text-[#0F172A] mb-4 flex items-center gap-2">
          <Gift size={20} />
          How Coins Work
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-3">
            <Check size={18} className="text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-[#0F172A]">1 Coin = 1 Message</p>
              <p className="text-gray-600">Send thoughtful messages</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Check size={18} className="text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-[#0F172A]">Coins Never Expire</p>
              <p className="text-gray-600">Use them whenever you want</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Check size={18} className="text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-[#0F172A]">Bulk Discounts</p>
              <p className="text-gray-600">Save up to 20% on larger packs</p>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction History */}
      <div>
        <h2 className="text-xl font-bold text-[#0F172A] mb-4 flex items-center gap-2">
          <History size={20} />
          Recent Transactions
        </h2>
        
        <div className="bg-white rounded-2xl shadow-md overflow-hidden">
          {transactionHistory.map((tx, index) => (
            <div
              key={tx.id}
              className={`flex items-center justify-between p-4 ${
                index < transactionHistory.length - 1 ? 'border-b border-gray-100' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  tx.type === 'purchase' ? 'bg-green-100' :
                  tx.type === 'bonus' ? 'bg-[#E9D5FF]' : 'bg-gray-100'
                }`}>
                  {tx.type === 'purchase' ? <CreditCard size={18} className="text-green-600" /> :
                   tx.type === 'bonus' ? <Gift size={18} className="text-[#0F172A]" /> :
                   <Coins size={18} className="text-gray-600" />}
                </div>
                <div>
                  <p className="font-medium text-[#0F172A]">{tx.description}</p>
                  <p className="text-xs text-gray-500">{tx.date}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold ${
                  tx.coins > 0 ? 'text-green-600' : 'text-gray-600'
                }`}>
                  {tx.coins > 0 ? '+' : ''}{tx.coins} coins
                </p>
                {tx.amount > 0 && (
                  <p className="text-xs text-gray-500">₹{tx.amount}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CreditsPage;
