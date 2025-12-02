import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import api from '@/services/api';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';

const Payouts = () => {
  const { user } = useAuth();
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState('');

  useEffect(() => {
    fetchPayouts();
  }, []);

  const fetchPayouts = async () => {
    try {
      const response = await api.get('/payouts/my-payouts');
      setPayouts(response.data);
    } catch (error) {
      toast.error('Failed to load payouts');
    } finally {
      setLoading(false);
    }
  };

  const handleRequestPayout = async () => {
    const credits = parseInt(amount);
    if (!credits || credits < 1000) {
      toast.error('Minimum payout is 1000 credits');
      return;
    }

    if (credits > user.credits_balance) {
      toast.error('Insufficient credits balance');
      return;
    }

    try {
      await api.post('/payouts/request', {
        amount_credits: credits,
        payment_method: 'bank_transfer',
        payment_details: { account: 'Bank account details' },
      });
      toast.success('Payout request submitted successfully!');
      setOpen(false);
      setAmount('');
      fetchPayouts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to request payout');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary">Pending</Badge>;
      case 'approved':
        return <Badge className="bg-blue-500">Approved</Badge>;
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'rejected':
        return <Badge variant="destructive">Rejected</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold mb-2">Payouts</h1>
            <p className="text-gray-600">Manage your payout requests</p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>Request Payout</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Request Payout</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Available Balance</p>
                  <p className="text-2xl font-bold">{user?.credits_balance || 0} credits</p>
                  <p className="text-sm text-gray-500">${((user?.credits_balance || 0) / 100).toFixed(2)} USD</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount (Credits)</Label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="Minimum 1000 credits"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    min="1000"
                  />
                  <p className="text-xs text-gray-500">
                    {amount ? `= $${(parseInt(amount) / 100).toFixed(2)} USD` : 'Enter amount'}
                  </p>
                </div>
                <Button onClick={handleRequestPayout} className="w-full">
                  Submit Request
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Payout History</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-gray-600">Loading payouts...</div>
            ) : payouts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No payouts yet</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Amount (Credits)</TableHead>
                    <TableHead>Amount (USD)</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Notes</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payouts.map((payout) => (
                    <TableRow key={payout.id}>
                      <TableCell>
                        {new Date(payout.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{payout.amount_credits}</TableCell>
                      <TableCell>${payout.amount_usd.toFixed(2)}</TableCell>
                      <TableCell>{getStatusBadge(payout.status)}</TableCell>
                      <TableCell className="text-sm text-gray-600">
                        {payout.admin_notes || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default Payouts;