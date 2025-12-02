import React, { useEffect, useState } from 'react';
import MainLayout from '@/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Shield, AlertTriangle, Ban } from 'lucide-react';
import api from '@/services/api';
import { toast } from 'sonner';

const AdminSecurity = () => {
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [bannedIps, setBannedIps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const fetchSecurityData = async () => {
    try {
      const [alertsRes, analyticsRes] = await Promise.all([
        api.get('/admin/security/fraud-alerts'),
        api.get('/admin/security/analytics'),
      ]);

      setFraudAlerts(alertsRes.data);
      setBannedIps(analyticsRes.data.banned_ips || []);
    } catch (error) {
      toast.error('Failed to load security data');
    } finally {
      setLoading(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await api.post(`/admin/security/fraud-alerts/${alertId}/resolve`);
      toast.success('Alert resolved');
      fetchSecurityData();
    } catch (error) {
      toast.error('Failed to resolve alert');
    }
  };

  const getSeverityBadge = (score) => {
    if (score >= 80) return <Badge variant="destructive">High Risk</Badge>;
    if (score >= 50) return <Badge className="bg-orange-500">Medium Risk</Badge>;
    return <Badge className="bg-yellow-500">Low Risk</Badge>;
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Security Dashboard</h1>
          <p className="text-gray-600">Monitor and manage platform security</p>
        </div>

        <Tabs defaultValue="fraud" className="space-y-4">
          <TabsList>
            <TabsTrigger value="fraud">
              <AlertTriangle className="h-4 w-4 mr-2" />
              Fraud Alerts
            </TabsTrigger>
            <TabsTrigger value="banned">
              <Ban className="h-4 w-4 mr-2" />
              Banned IPs
            </TabsTrigger>
            <TabsTrigger value="analytics">
              <Shield className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          {/* Fraud Alerts Tab */}
          <TabsContent value="fraud">
            <Card>
              <CardHeader>
                <CardTitle>Active Fraud Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8 text-gray-600">Loading alerts...</div>
                ) : fraudAlerts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No active fraud alerts</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>User ID</TableHead>
                        <TableHead>Risk Score</TableHead>
                        <TableHead>Rule Triggered</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fraudAlerts.map((alert) => (
                        <TableRow key={alert.id}>
                          <TableCell className="font-mono text-sm">{alert.user_id}</TableCell>
                          <TableCell>{getSeverityBadge(alert.risk_score)}</TableCell>
                          <TableCell>{alert.rule_triggered}</TableCell>
                          <TableCell>
                            {new Date(alert.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleResolveAlert(alert.id)}
                            >
                              Resolve
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Banned IPs Tab */}
          <TabsContent value="banned">
            <Card>
              <CardHeader>
                <CardTitle>Banned IP Addresses</CardTitle>
              </CardHeader>
              <CardContent>
                {bannedIps.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No banned IPs</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>IP Address</TableHead>
                        <TableHead>Reason</TableHead>
                        <TableHead>Banned Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bannedIps.map((ip, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-mono">{ip.address}</TableCell>
                          <TableCell>{ip.reason}</TableCell>
                          <TableCell>{new Date(ip.banned_at).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Button size="sm" variant="outline">
                              Unban
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Failed Logins</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">24</div>
                  <p className="text-sm text-gray-500 mt-1">Last 24 hours</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Blocked Requests</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">156</div>
                  <p className="text-sm text-gray-500 mt-1">Last 24 hours</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>2FA Enabled</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">45%</div>
                  <p className="text-sm text-gray-500 mt-1">Of all users</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
};

export default AdminSecurity;