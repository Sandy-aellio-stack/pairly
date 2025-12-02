import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

const BuyCredits = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const packages = [
    { credits: 1000, price: 9.99, popular: false },
    { credits: 5000, price: 39.99, popular: true },
    { credits: 10000, price: 74.99, popular: false },
    { credits: 25000, price: 174.99, popular: false },
  ];

  const handlePurchase = async (credits, price) => {
    setLoading(true);
    try {
      const response = await api.post('/payments/checkout', {
        credits_amount: credits,
        provider: 'stripe',
      });

      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      toast.error('Failed to initiate payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">Buy Credits</h1>
          <p className="text-gray-600">Choose a package that suits your needs</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {packages.map((pkg) => (
            <Card
              key={pkg.credits}
              className={`relative ${pkg.popular ? 'border-pink-500 border-2' : ''}`}
            >
              {pkg.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-pink-500">Most Popular</Badge>
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-center">
                  <div className="text-3xl font-bold text-pink-600">
                    {pkg.credits.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">Credits</div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-4xl font-bold">${pkg.price}</div>
                  <div className="text-sm text-gray-500">one-time payment</div>
                </div>

                <ul className="space-y-2 text-sm">
                  <li className="flex items-center">
                    <Check className="h-4 w-4 text-green-500 mr-2" />
                    <span>Never expires</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-4 w-4 text-green-500 mr-2" />
                    <span>Instant delivery</span>
                  </li>
                  <li className="flex items-center">
                    <Check className="h-4 w-4 text-green-500 mr-2" />
                    <span>Secure payment</span>
                  </li>
                </ul>

                <Button
                  className="w-full"
                  onClick={() => handlePurchase(pkg.credits, pkg.price)}
                  disabled={loading}
                >
                  {loading ? 'Processing...' : 'Buy Now'}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="mt-8">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">Payment Information</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• All payments are processed securely through Stripe</li>
              <li>• Credits never expire and can be used anytime</li>
              <li>• 1 credit = $0.01 USD</li>
              <li>• Refunds available within 7 days of purchase</li>
              <li>• For support, contact support@pairly.com</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default BuyCredits;