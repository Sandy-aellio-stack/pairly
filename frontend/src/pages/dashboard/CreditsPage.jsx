import { useState, useEffect } from 'react';
import { Coins, CreditCard, History, Check, IndianRupee } from 'lucide-react';
import useAuthStore from '@/store/authStore';
import { paymentsAPI, creditsAPI } from '@/services/api';

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
      console.log('Failed to load data');
    }
  };

  const handlePurchase = async () => {
    if (!selectedPackage) return;
    setLoading(true);

    try {
      const orderResponse = await paymentsAPI.createOrder(selectedPackage.id);
      const { order_id, amount, key_id } = orderResponse.data;

      // Initialize Razorpay
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
            alert('Payment successful! Coins added to your account.');
          } catch (e) {
            alert('Payment verification failed');
          }
        },
        prefill: {},
        theme: {
          color: '#7B5CFF',
        },
      };

      // Check if Razorpay is available
      if (typeof window.Razorpay !== 'undefined') {
        const razorpay = new window.Razorpay(options);
        razorpay.open();
      } else {
        alert('Razorpay not loaded. Please refresh the page.');
      }
    } catch (e) {
      console.log('Failed to create order:', e);
      alert('Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Credits</h1>

      {/* Balance Card */}
      <div className="card-dark bg-gradient-to-br from-purple-500/20 to-pink-500/20 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/60 mb-1">Current Balance</p>
            <div className="text-5xl font-bold gradient-text">{credits}</div>
            <p className="text-white/40 text-sm">coins available</p>
          </div>
          <div className="w-20 h-20 rounded-full bg-purple-500/30 flex items-center justify-center">
            <Coins size={40} className="text-purple-400" />
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
              : 'bg-white/5 text-white/60 hover:bg-white/10'
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
              : 'bg-white/5 text-white/60 hover:bg-white/10'
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
            {packages.map((pkg) => (
              <button
                key={pkg.id}
                onClick={() => setSelectedPackage(pkg)}
                className={`card-dark text-left transition-all ${
                  selectedPackage?.id === pkg.id
                    ? 'border-purple-500 ring-2 ring-purple-500/20'
                    : 'hover:border-purple-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl font-bold gradient-text">₹{pkg.amount_inr}</span>
                  {selectedPackage?.id === pkg.id && (
                    <div className="w-6 h-6 rounded-full bg-purple-500 flex items-center justify-center">
                      <Check size={14} />
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Coins size={18} className="text-purple-400" />
                  <span className="text-lg">{pkg.credits} coins</span>
                </div>
                <p className="text-white/40 text-sm mt-2">
                  ₹{(pkg.amount_inr / pkg.credits).toFixed(2)} per coin
                </p>
              </button>
            ))}
          </div>

          {/* Purchase Button */}
          <button
            onClick={handlePurchase}
            disabled={!selectedPackage || loading}
            className="btn-primary w-full py-4 flex items-center justify-center gap-3 disabled:opacity-50"
          >
            <IndianRupee size={20} />
            {loading
              ? 'Processing...'
              : selectedPackage
              ? `Pay ₹${selectedPackage.amount_inr}`
              : 'Select a package'}
          </button>

          <p className="text-center text-white/40 text-sm mt-4">
            Secure payment powered by Razorpay
          </p>
        </>
      ) : (
        /* History */
        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-10 text-white/60">
              No transaction history yet
            </div>
          ) : (
            history.map((tx) => (
              <div
                key={tx.id}
                className="card-dark flex items-center justify-between py-4"
              >
                <div>
                  <p className="font-medium">
                    {tx.reason === 'signup_bonus' && '🎁 Signup Bonus'}
                    {tx.reason === 'message_sent' && '✉️ Message Sent'}
                    {tx.reason === 'credit_purchase' && '💳 Credit Purchase'}
                    {tx.reason === 'refund' && '🔄 Refund'}
                  </p>
                  <p className="text-white/40 text-sm">
                    {new Date(tx.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className={`text-lg font-bold ${
                  tx.amount > 0 ? 'text-green-400' : 'text-red-400'
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
