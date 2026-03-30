import React, { useEffect, useState } from 'react';
import { Shield, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { authAPI } from '../../services/api';
import { getSocket } from '../../services/socket';
import useAuthStore from '../../store/authStore';

const LoginApprovalModal = () => {
    const { logout, user } = useAuthStore();
    const [request, setRequest] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const socket = getSocket();

    useEffect(() => {
        if (!socket) return;

        const handleApprovalRequest = (data) => {
            console.log('Login approval request received:', data);
            setRequest(data);
        };

        const handleForceLogout = (data) => {
            toast.info(data.message || 'You have been logged out because of a login on another device.');
            logout();
        };

        socket.on('login_approval_request', handleApprovalRequest);
        socket.on('force_logout', handleForceLogout);

        return () => {
            socket.off('login_approval_request', handleApprovalRequest);
            socket.off('force_logout', handleForceLogout);
        };
    }, [socket, logout]);

    const handleApprove = async () => {
        if (!request) return;
        setIsProcessing(true);
        try {
            await authAPI.approveLogin(request.pending_session_id);
            toast.success('Login approved. You will be logged out shortly.');
            setRequest(null);
        } catch (error) {
            toast.error('Failed to approve login');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDeny = async () => {
        if (!request) return;
        setIsProcessing(true);
        try {
            await authAPI.denyLogin(request.pending_session_id);
            toast.info('Login request denied.');
            setRequest(null);
        } catch (error) {
            toast.error('Failed to deny login');
        } finally {
            setIsProcessing(false);
        }
    };

    if (!request) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in duration-300">
                <div className="p-6 text-center">
                    <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Shield className="text-pink-600" size={32} />
                    </div>

                    <h3 className="text-xl font-bold text-gray-900 mb-2">Security Alert</h3>
                    <p className="text-gray-600 mb-6">
                        A new device is trying to sign in to your Luveloop account.
                        Is this you?
                    </p>

                    <div className="bg-gray-50 rounded-xl p-4 mb-6 text-sm text-left flex items-start gap-3">
                        <AlertCircle className="text-gray-400 shrink-0" size={20} />
                        <div>
                            <p className="font-semibold text-gray-700">New Login Attempt</p>
                            <p className="text-gray-500">Device ID: {request.new_device_id?.substring(0, 8)}...</p>
                            <p className="text-gray-500 mt-1 italic text-xs">If you approve, you will be logged out of this device.</p>
                        </div>
                    </div>

                    <div className="flex flex-col gap-3">
                        <button
                            onClick={handleApprove}
                            disabled={isProcessing}
                            className="w-full py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            <CheckCircle size={20} />
                            Yes, it's me (Approve)
                        </button>
                        <button
                            onClick={handleDeny}
                            disabled={isProcessing}
                            className="w-full py-3 border-2 border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            <XCircle size={20} />
                            No, deny request
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginApprovalModal;
