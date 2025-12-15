import { useState, useEffect } from 'react';
import { Coins, CreditCard, History, Check, IndianRupee, Sparkles, TrendingUp } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { paymentsAPI, creditsAPI } from '@/services/api';
import { toast } from 'sonner';

const CreditsPage = () => {
  const { credits, refreshCredits } = useAuthStore();
  const [packages, setPackages] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('buy');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [packagesRes, historyRes] = await Promise.all([
        paymentsAPI.getPackages(),
        creditsAPI.getHistory(20),
      ]);
      setPackages(packagesRes.data.packages || []);
      setHistory(historyRes.data.transactions || []);
    } catch (e) {
      // Mock packages
      setPackages([
        { id: '1', credits: 50, amount_inr: 49 },
        { id: '2', credits: 100, amount_inr: 89 },
        { id: '3', credits: 250, amount_inr: 199 },
        { id: '4', credits: 500, amount_inr: 349 },
      ]);
    }
  };

  const handlePurchase = async () => {
    if (!selectedPackage) return;
    setLoading(true);

    try {
      const orderResponse = await paymentsAPI.createOrder(selectedPackage.id);
      const { order_id, amount, key_id } = orderResponse.data;

      const options = {
        key: key_id,
        amount: amount,
        currency: 'INR',
        name: 'TrueBond',
        description: `Purchase ${selectedPackage.credits} coins`,
        order_id: order_id,
        handler: async (response) => {
          try {
            await paymentsAPI.verifyPayment({
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            await refreshCredits();
            await loadData();
            setSelectedPackage(null);
            toast.success('Payment successful! Coins added.');
          } catch (e) {
            toast.error('Payment verification failed');
          }
        },
        theme: {
          color: '#7B5CFF',
        },
      };

      if (typeof window.Razorpay !== 'undefined') {
        const razorpay = new window.Razorpay(options);
        razorpay.open();
      } else {
        toast.error('Razorpay not loaded. Please refresh.');
      }
    } catch (e) {
      toast.error('Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Wallet</h1>

      {/* Balance Card */}
      <div className="card bg-gradient-to-br from-purple-500 to-pink-500 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/80 mb-1">Current Balance</p>
            <div className="text-5xl font-bold">{credits}</div>
            <p className="text-white/60 text-sm mt-1">coins available</p>
          </div>
          <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center">
            <Coins size={40} className="text-white" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setTab('buy')}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            tab === 'buy'
              ? 'bg-purple-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <CreditCard size={18} className="inline mr-2" />
          Buy Coins
        </button>
        <button
          onClick={() => setTab('history')}
          className={`px-6 py-3 rounded-xl font-medium transition-all ${
            tab === 'history'
              ? 'bg-purple-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
          }`}
        >
          <History size={18} className="inline mr-2" />
          History
        </button>
      </div>

      {tab === 'buy' ? (
        <>
          {/* Packages */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            {packages.map((pkg, i) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
                className={`card text-left transition-all relative overflow-hidden ${
                  selectedPackage?.id === pkg.id
                    ? 'border-purple-500 ring-2 ring-purple-200'
                    : 'hover:border-purple-300'
                }`}
              >
                {i === 2 && (
                  <div className="absolute top-2 right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <Sparkles size={10} /> Popular
                  </div>
                )}
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-bold text-gray-900">₹{pkg.amount_inr}</span>
                  {selectedPackage?.id === pkg.id && (
                    <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center">
                      <Check size={14} className="text-white" />
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Coins size={18} className="text-purple-500" />
                  <span className="text-lg text-gray-700">{pkg.credits} coins</span>
                </div>
                <p className="text-gray-400 text-sm mt-2">
                  ₹{(pkg.amount_inr / pkg.credits).toFixed(2)} per coin
                </p>
              </button>
            ))}
          </div>

          {/* Purchase Button */}
          <button
            onClick={handlePurchase}
            disabled={!selectedPackage || loading}
            className="btn-primary w-full py-4 flex items-center justify-center gap-3 disabled:opacity-50 text-lg"
          >
            <IndianRupee size={20} />
            {loading
              ? 'Processing...'
              : selectedPackage
              ? `Pay ₹${selectedPackage.amount_inr}`
              : 'Select a package'}
          </button>

          <p className="text-center text-gray-400 text-sm mt-4">
            🔒 Secure payment powered by Razorpay
          </p>
        </>
      ) : (
        /* History */
        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-10 card">
              <History size={48} className="text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No transaction history yet</p>
            </div>
          ) : (
            history.map((tx) => (
              <div
                key={tx.id}
                className="card flex items-center justify-between py-4"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    tx.amount > 0 ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    <TrendingUp size={18} className={tx.amount > 0 ? 'text-green-600' : 'text-red-600 rotate-180'} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {tx.reason === 'signup_bonus' && '🎁 Signup Bonus'}
                      {tx.reason === 'message_sent' && '✉️ Message Sent'}
                      {tx.reason === 'credit_purchase' && '💳 Credit Purchase'}
                      {tx.reason === 'refund' && '🔄 Refund'}
                    </p>
                    <p className="text-gray-400 text-sm">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className={`text-lg font-bold ${
                  tx.amount > 0 ? 'text-green-600' : 'text-red-500'
                }`}>
                  {tx.amount > 0 ? '+' : ''}{tx.amount}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default CreditsPage;
