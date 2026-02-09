import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, PhoneOff, Video } from 'lucide-react';
import { toast } from 'sonner';
import { getSocket, onIncomingCall, rejectCall } from '@/services/socket';

const IncomingCallModal = () => {
  const navigate = useNavigate();
  const [incomingCall, setIncomingCall] = useState(null);

  const handleIncomingCall = useCallback((data) => {
    setIncomingCall(data);
    toast.info(`Incoming ${data.call_type} call...`);
  }, []);

  useEffect(() => {
    const socket = getSocket();
    if (!socket?.connected) return;

    onIncomingCall(handleIncomingCall);

    return () => {
      socket?.off('incoming_call', handleIncomingCall);
    };
  }, [handleIncomingCall]);

  const handleAccept = () => {
    if (!incomingCall) return;
    
    const offer = encodeURIComponent(JSON.stringify(incomingCall.offer));
    navigate(
      `/call/${incomingCall.caller_id}?type=${incomingCall.call_type}&incoming=true&callId=${incomingCall.call_id}&offer=${offer}`
    );
    setIncomingCall(null);
  };

  const handleReject = async () => {
    if (!incomingCall) return;
    
    try {
      await rejectCall(incomingCall.call_id, 'rejected');
    } catch (error) {
      console.error('Error rejecting call:', error);
    }
    
    setIncomingCall(null);
    toast.info('Call rejected');
  };

  if (!incomingCall) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 lg:cursor-none">
      <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 text-center shadow-2xl">
        <div className="w-20 h-20 rounded-full bg-[#E9D5FF] mx-auto mb-4 flex items-center justify-center animate-pulse">
          {incomingCall.call_type === 'video' ? (
            <Video size={32} className="text-[#0F172A]" />
          ) : (
            <Phone size={32} className="text-[#0F172A]" />
          )}
        </div>
        
        <h3 className="text-xl font-bold text-[#0F172A] mb-2">Incoming Call</h3>
        <p className="text-gray-600 mb-6">
          Someone is calling you ({incomingCall.call_type})
        </p>
        
        <div className="flex justify-center gap-6">
          <button
            onClick={handleReject}
            className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors"
          >
            <PhoneOff size={28} className="text-white" />
          </button>
          <button
            onClick={handleAccept}
            className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center hover:bg-green-600 transition-colors"
          >
            <Phone size={28} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default IncomingCallModal;
