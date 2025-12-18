import { useState, useEffect, useRef } from 'react';
import { Phone, PhoneOff, Video, VideoOff, Mic, MicOff, Volume2, VolumeX, Loader2, Coins } from 'lucide-react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';

const CallPage = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const callType = searchParams.get('type') || 'audio'; // 'audio' or 'video'
  const { user, refreshCredits } = useAuthStore();
  
  const [isConnecting, setIsConnecting] = useState(true);
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(callType === 'audio');
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [coinsUsed, setCoinsUsed] = useState(0);
  
  const timerRef = useRef(null);
  const coinDeductionRef = useRef(null);

  const AUDIO_COST_PER_MIN = 5;
  const VIDEO_COST_PER_MIN = 10;
  const currentCostPerMin = callType === 'video' ? VIDEO_COST_PER_MIN : AUDIO_COST_PER_MIN;

  // Check if user has enough credits
  useEffect(() => {
    if ((user?.credits_balance || 0) < currentCostPerMin) {
      toast.error(`You need at least ${currentCostPerMin} coins to start a ${callType} call`);
      navigate('/dashboard/credits');
    }
  }, []);

  // Simulate connection
  useEffect(() => {
    const connectionTimer = setTimeout(() => {
      setIsConnecting(false);
      toast.success('Connected!');
      startCallTimer();
    }, 2000);

    return () => clearTimeout(connectionTimer);
  }, []);

  const startCallTimer = () => {
    // Timer for duration display
    timerRef.current = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);

    // Coin deduction every minute
    coinDeductionRef.current = setInterval(() => {
      setCoinsUsed(prev => prev + currentCostPerMin);
      toast.info(`-${currentCostPerMin} coins (${callType} call)`);
    }, 60000); // Every minute
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const endCall = () => {
    clearInterval(timerRef.current);
    clearInterval(coinDeductionRef.current);
    
    // Final coin deduction for partial minute
    const partialMinutes = Math.ceil(callDuration / 60);
    const totalCost = partialMinutes * currentCostPerMin;
    
    toast.success(`Call ended. Total: ${totalCost} coins for ${formatDuration(callDuration)}`);
    refreshCredits();
    navigate('/dashboard/chat');
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0F172A] to-[#1E293B] flex flex-col items-center justify-center">
      {/* Caller Info */}
      <div className="text-center mb-8">
        <div className="w-32 h-32 rounded-full bg-[#E9D5FF] mx-auto mb-4 flex items-center justify-center overflow-hidden">
          <span className="text-5xl text-[#0F172A]">U</span>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">User</h2>
        
        {isConnecting ? (
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Connecting...</span>
          </div>
        ) : (
          <div className="text-gray-400">
            <p className="text-2xl font-mono mb-1">{formatDuration(callDuration)}</p>
            <p className="text-sm flex items-center justify-center gap-1">
              <Coins size={14} />
              {currentCostPerMin} coins/min
            </p>
          </div>
        )}
      </div>

      {/* Video Preview (if video call) */}
      {callType === 'video' && !isVideoOff && (
        <div className="absolute top-4 right-4 w-32 h-44 bg-gray-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="w-full h-full bg-gray-700 flex items-center justify-center">
            <span className="text-gray-500 text-sm">Your camera</span>
          </div>
        </div>
      )}

      {/* Call Controls */}
      <div className="flex items-center gap-4">
        {/* Mute */}
        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
            isMuted ? 'bg-red-500' : 'bg-white/20'
          }`}
        >
          {isMuted ? <MicOff size={24} className="text-white" /> : <Mic size={24} className="text-white" />}
        </button>

        {/* Video Toggle (for video calls) */}
        {callType === 'video' && (
          <button
            onClick={() => setIsVideoOff(!isVideoOff)}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
              isVideoOff ? 'bg-red-500' : 'bg-white/20'
            }`}
          >
            {isVideoOff ? <VideoOff size={24} className="text-white" /> : <Video size={24} className="text-white" />}
          </button>
        )}

        {/* End Call */}
        <button
          onClick={endCall}
          className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors"
        >
          <PhoneOff size={28} className="text-white" />
        </button>

        {/* Speaker */}
        <button
          onClick={() => setIsSpeakerOn(!isSpeakerOn)}
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
            !isSpeakerOn ? 'bg-red-500' : 'bg-white/20'
          }`}
        >
          {isSpeakerOn ? <Volume2 size={24} className="text-white" /> : <VolumeX size={24} className="text-white" />}
        </button>
      </div>

      {/* Coins Info */}
      <div className="absolute bottom-8 left-0 right-0 text-center">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
          <Coins size={18} className="text-yellow-400" />
          <span className="text-white">Balance: {(user?.credits_balance || 0) - coinsUsed} coins</span>
        </div>
      </div>
    </div>
  );
};

export default CallPage;
