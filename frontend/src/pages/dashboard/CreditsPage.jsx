import { useState, useEffect } from 'react';
import { Coins, Check, Sparkles, CreditCard, History, Gift, Loader2, MessageCircle, Phone, Video } from 'lucide-react';
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

  // Default pricing tiers (fallback)
  const defaultTiers = [
    { id: 'starter', name: 'Starter', coins: 100, price: 100, pricePerCoin: 1, discount: 0 },
    { id: 'popular', name: 'Popular', coins: 500, price: 450, pricePerCoin: 0.9, discount: 10, popular: true },
    { id: 'premium', name: 'Premium', coins: 1000, price: 800, pricePerCoin: 0.8, discount: 20 },
  ];

  // Pricing constants
  const MESSAGE_COST = 1;
  const AUDIO_COST = 5;
  const VIDEO_COST = 10;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch packages and transaction history in parallel
      const [packagesRes, historyRes] = await Promise.all([
        paymentsAPI.getPackages().catch(() => ({ data: { packages: [] } })),
        creditsAPI.getHistory().catch(() => ({ data: { transactions: [] } }))
      ]);

      // Process packages
      if (packagesRes.data.packages && packagesRes.data.packages.length > 0) {
        const formattedPackages = packagesRes.data.packages.map((pkg, idx) => ({
          id: pkg.id,
          name: pkg.label || `${pkg.credits} Coins`,
          coins: pkg.credits,
          price: pkg.amount_inr,
          pricePerCoin: pkg.amount_inr / pkg.credits,
          discount: Math.round((1 - (pkg.amount_inr / pkg.credits)) * 100), // Calculate discount
          popular: idx === 1, // Second package is popular
        }));
        setPackages(formattedPackages);
      } else {
        setPackages(defaultTiers);
      }

      // Process transactions
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
      
      if (response.data.order_id && window.Razorpay) {
        const options = {
          key: response.data.key_id || 'rzp_test_key',
          amount: tier.price * 100, // Razorpay expects amount in paise
          currency: 'INR',
          name: 'TrueBond',
          description: `${tier.coins} Coins - ${tier.name} Pack`,
          order_id: response.data.order_id,
          handler: async function(razorpayResponse) {
            try {
              await paymentsAPI.verifyPayment({
                razorpay_order_id: razorpayResponse.razorpay_order_id,
                razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                razorpay_signature: razorpayResponse.razorpay_signature,
              });
              toast.success(`Successfully purchased ${tier.coins} coins!`);
              refreshCredits();
              fetchData(); // Refresh transaction history
            } catch (err) {
              toast.error('Payment verification failed');
            }
          },
          prefill: {
            email: user?.email || '',
            contact: user?.mobile_number || '',
          },
          theme: {
            color: '#0F172A'
          }
        };
        
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        toast.info(`Demo: Would purchase ${tier.coins} coins for ₹${tier.price}`);
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
    <div className="max-w-4xl mx-auto px-4">
      {/* Balance Card */}
      <div className="bg-gradient-to-r from-[#0F172A] to-[#1E293B] rounded-3xl p-8 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/70 text-sm mb-1">Your Balance</p>
            <div className="flex items-center gap-3">
              <Coins size={40} className="text-yellow-400" />
              <span className="text-5xl font-bold">{user?.credits_balance || 0}</span>
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
              key={tier.id || index}
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
                } ${isPurchasing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isPurchasing ? 'Processing...' : 'Buy Now'}
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
