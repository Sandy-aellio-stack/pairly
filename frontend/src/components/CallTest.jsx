import { useState, useEffect } from 'react';
import { Phone } from 'lucide-react';
import { getSocket, callUser, onIncomingCall } from '@/services/socket';

const CallTest = () => {
  const [socket, setSocket] = useState(null);
  const [otherUserId, setOtherUserId] = useState('test_user_2');
  const [logs, setLogs] = useState([]);

  const addLog = (message) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  useEffect(() => {
    const s = getSocket();
    setSocket(s);
    
    if (s?.connected) {
      addLog('Socket connected');
      
      // Listen for incoming calls
      s.on('incoming_call', (data) => {
        addLog(`🔔 INCOMING CALL: ${JSON.stringify(data)}`);
        alert('Incoming call received!');
      });
      
      // Listen for call failed
      s.on('call_failed', (data) => {
        addLog(`❌ CALL FAILED: ${JSON.stringify(data)}`);
      });
    } else {
      addLog('Socket not connected');
    }

    return () => {
      s?.off('incoming_call');
      s?.off('call_failed');
    };
  }, []);

  const handleCall = () => {
    if (!socket?.connected) {
      addLog('❌ Socket not connected');
      return;
    }

    addLog(`📞 Calling ${otherUserId}...`);
    
    // Use the exact format requested
    socket.emit('call_user', {
      user_id: otherUserId,
      call_type: 'audio'
    });
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Socket.IO Call Test</h2>
      
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">Target User ID:</label>
        <input
          type="text"
          value={otherUserId}
          onChange={(e) => setOtherUserId(e.target.value)}
          className="w-full p-2 border rounded"
          placeholder="Enter user ID to call"
        />
      </div>

      <button
        onClick={handleCall}
        className="flex items-center gap-2 bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600"
      >
        <Phone size={20} />
        Call User
      </button>

      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">Logs:</h3>
        <div className="bg-gray-100 p-4 rounded-lg h-64 overflow-y-auto font-mono text-sm">
          {logs.map((log, i) => (
            <div key={i} className="mb-1">{log}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CallTest;
