import React from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { XCircle } from 'lucide-react';

const PaymentFailed = () => {
  const navigate = useNavigate();

  return (
    <MainLayout>
      <div className="max-w-md mx-auto mt-16">
        <Card>
          <CardContent className="pt-12 pb-8 text-center space-y-4">
            <XCircle className="h-20 w-20 text-red-500 mx-auto" />
            <h1 className="text-3xl font-bold">Payment Failed</h1>
            <p className="text-gray-600">
              We couldn't process your payment. Please try again or contact support if the problem persists.
            </p>
            <div className="space-y-2 pt-4">
              <Button className="w-full" onClick={() => navigate('/buy-credits')}>
                Try Again
              </Button>
              <Button variant="outline" className="w-full" onClick={() => navigate('/')}>
                Go to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default PaymentFailed;