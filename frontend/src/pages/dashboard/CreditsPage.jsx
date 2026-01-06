import { useState, useEffect } from 'react';
import { Coins, Check, Sparkles, CreditCard, History, Gift, Loader2, MessageCircle, Phone, Video, Info } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { creditsAPI, paymentsAPI } from '@/services/api';
import { toast } from 'sonner';

const CreditsPage = () => {
  const { user, refreshCredits } = useAuthStore();
  const [selectedTier, setSelectedTier] = useState(1);
  const [transactions, setTransactions] = useState([]);
  const [packages, setPackages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isPurchasing, setIsPurchasing] = useState(false);

  const defaultTiers = [
    { 
      id: 'starter', 
      name: 'Starter', 
      coins: 100, 
      price: 100, 
      pricePerCoin: 1, 
      discount: 0,
      features: [
        '100 coins',
        '1 per coin',
        'Basic matching',
        'Profile verification',
      ],
    },
    { 
      id: 'popular', 
      name: 'Popular', 
      coins: 500, 
      price: 450, 
      pricePerCoin: 0.9, 
      discount: 10, 
      popular: true,
      features: [
        '500 coins',
        '0.90 per coin (10% off)',
        'Priority matching',
        'Advanced filters',
        'Profile boost',
      ],
    },
    { 
      id: 'premium', 
      name: 'Premium', 
      coins: 1000, 
      price: 800, 
      pricePerCoin: 0.8, 
      discount: 20,
      features: [
        '1000 coins',
        '0.80 per coin (20% off)',
        'Unlimited matching',
        'All features included',
        'VIP support',
      ],
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [packagesRes, historyRes] = await Promise.all([
        paymentsAPI.getPackages().catch(() => ({ data: { packages: [] } })),
        creditsAPI.getHistory().catch(() => ({ data: { transactions: [] } }))
      ]);

      if (packagesRes.data.packages && packagesRes.data.packages.length > 0) {
        const formattedPackages = packagesRes.data.packages.map((pkg, idx) => ({
          id: pkg.id,
          name: pkg.label || `${pkg.credits} Coins`,
          coins: pkg.credits,
          price: pkg.amount_inr,
          pricePerCoin: pkg.amount_inr / pkg.credits,
          discount: Math.round((1 - (pkg.amount_inr / pkg.credits)) * 100),
          popular: idx === 1,
          features: defaultTiers[idx]?.features || defaultTiers[0].features,
        }));
        setPackages(formattedPackages);
      } else {
        setPackages(defaultTiers);
      }

      if (historyRes.data.transactions) {
        const formattedTx = historyRes.data.transactions.map(tx => ({
          id: tx.id,
          type: tx.reason === 'SIGNUP_BONUS' ? 'bonus' : tx.reason === 'PURCHASE' ? 'purchase' : 'spent',
          amount: tx.amount > 0 ? tx.amount : 0,
          coins: tx.amount,
          date: new Date(tx.created_at).toLocaleDateString(),
          description: tx.description || tx.reason
        }));
        setTransactions(formattedTx);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setPackages(defaultTiers);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePurchase = async (tier) => {
    setIsPurchasing(true);
    try {
      const response = await paymentsAPI.createOrder(tier.id);
      
      if (response.data.payment_intent_id) {
        const isMockOrder = response.data.payment_intent_id.startsWith('pi_mock_');
        
        if (isMockOrder) {
          try {
            await paymentsAPI.verifyPayment({
              payment_intent_id: response.data.payment_intent_id,
            });
            toast.success(`Successfully purchased ${tier.coins} coins!`);
            refreshCredits();
            fetchData();
          } catch (err) {
            toast.error('Demo purchase failed');
          }
        } else {
          toast.info('Stripe payment integration coming soon. Please contact support.');
        }
      } else {
        toast.error('Failed to create order');
      }
    } catch (error) {
      toast.error('Failed to create order. Please try again.');
    } finally {
      setIsPurchasing(false);
    }
  };

  const pricingTiers = packages.length > 0 ? packages : defaultTiers;

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 flex items-center justify-center h-[60vh]">
        <Loader2 className="w-12 h-12 animate-spin text-[#0F172A]" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4">
      <div className="text-center max-w-3xl mx-auto mb-8">
        <span className="text-sm font-semibold text-[#7C3AED] uppercase tracking-wider">Your Coins</span>
        <h1 className="text-3xl md:text-4xl font-bold text-[#0F172A] mt-2 mb-2">
          Simple, Fair Pricing
        </h1>
        <p className="text-lg text-gray-600">
          Pay only for what you use. No subscriptions, no hidden fees.
        </p>
      </div>

      <div className="bg-gradient-to-r from-[#0F172A] to-[#1E293B] rounded-3xl p-8 text-white mb-8 max-w-xl mx-auto">
        <div className="text-center mb-6">
          <p className="text-white/70 text-sm mb-2">Your Current Balance</p>
          <div className="flex items-center justify-center gap-3">
            <Coins size={48} className="text-yellow-400" />
            <span className="text-6xl font-bold">{user?.credits_balance || 0}</span>
            <span className="text-white/70 text-xl">coins</span>
          </div>
        </div>
      </div>

      <div className="bg-[#E9D5FF]/30 rounded-2xl p-6 max-w-xl mx-auto mb-12">
        <h4 className="font-semibold text-[#0F172A] mb-4 text-center">How Coins Work</h4>
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

      <div className="mb-12">
        <h2 className="text-2xl font-bold text-[#0F172A] mb-6 text-center">Buy Coins</h2>
        
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {pricingTiers.map((tier, index) => (
            <button
              key={tier.id || index}
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
                {(tier.features || []).map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <Check size={16} className={tier.popular ? 'text-green-400 mr-2 flex-shrink-0 mt-0.5' : 'text-green-500 mr-2 flex-shrink-0 mt-0.5'} />
                    <span className={`text-sm ${tier.popular ? 'text-white/90' : 'text-gray-600'}`}>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  handlePurchase(tier);
                }}
                className={`w-full py-2.5 rounded-xl font-semibold text-center transition-all cursor-pointer ${
                  tier.popular
                    ? 'bg-white text-[#0F172A] hover:bg-gray-100'
                    : 'bg-[#0F172A] text-white hover:shadow-lg'
                } ${isPurchasing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isPurchasing ? 'Processing...' : 'Buy Now'}
              </div>
            </button>
          ))}
        </div>
      </div>
      
      <div className="max-w-3xl mx-auto bg-gray-50 rounded-2xl p-6 border border-gray-200 mb-12">
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

      <div className="max-w-3xl mx-auto">
        <h2 className="text-xl font-bold text-[#0F172A] mb-4 flex items-center gap-2">
          <History size={20} />
          Recent Transactions
        </h2>
        
        <div className="bg-white rounded-2xl shadow-md overflow-hidden">
          {transactions.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <History size={32} className="mx-auto mb-2 text-gray-300" />
              <p>No transactions yet</p>
            </div>
          ) : (
            transactions.map((tx, index) => (
              <div
                key={tx.id}
                className={`flex items-center justify-between p-4 ${
                  index < transactions.length - 1 ? 'border-b border-gray-100' : ''
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
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default CreditsPage;
