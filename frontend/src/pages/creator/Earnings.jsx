import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import api from '@/services/api';
import { toast } from 'sonner';

const Earnings = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const response = await api.get('/credits/transactions');
      setTransactions(response.data);
    } catch (error) {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const getTransactionBadge = (type) => {
    switch (type) {
      case 'credit':
        return <Badge className="bg-green-500">Credit</Badge>;
      case 'debit':
        return <Badge variant="destructive">Debit</Badge>;
      case 'purchase':
        return <Badge className="bg-blue-500">Purchase</Badge>;
      case 'payout':
        return <Badge variant="secondary">Payout</Badge>;
      default:
        return <Badge>{type}</Badge>;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Earnings History</h1>
          <p className="text-gray-600">View all your credit transactions</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Transaction History</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-gray-600">Loading transactions...</div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No transactions yet</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell>
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{getTransactionBadge(transaction.transaction_type)}</TableCell>
                      <TableCell>{transaction.description}</TableCell>
                      <TableCell className={`text-right font-semibold ${
                        transaction.amount > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.amount > 0 ? '+' : ''}{transaction.amount}
                      </TableCell>
                      <TableCell className="text-right">{transaction.balance_after}</TableCell>
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

export default Earnings;