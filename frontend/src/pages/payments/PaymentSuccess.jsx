import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';

const PaymentSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const credits = searchParams.get('credits') || '0';

  return (
    <MainLayout>
      <div className="max-w-md mx-auto mt-16">
        <Card>
          <CardContent className="pt-12 pb-8 text-center space-y-4">
            <CheckCircle className="h-20 w-20 text-green-500 mx-auto" />
            <h1 className="text-3xl font-bold">Payment Successful!</h1>
            <p className="text-gray-600">
              Your payment has been processed successfully.
            </p>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Credits Added</p>
              <p className="text-3xl font-bold text-green-600">{credits}</p>
            </div>
            <div className="space-y-2 pt-4">
              <Button className="w-full" onClick={() => navigate('/')}>
                Go to Home
              </Button>
              <Button variant="outline" className="w-full" onClick={() => navigate('/discovery')}>
                Start Exploring
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default PaymentSuccess;