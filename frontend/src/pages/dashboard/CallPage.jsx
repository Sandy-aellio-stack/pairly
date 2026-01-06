import { useState, useEffect, useRef, useCallback } from 'react';
import { Phone, PhoneOff, Video, VideoOff, Mic, MicOff, Volume2, VolumeX, Loader2, Coins } from 'lucide-react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import useAuthStore from '@/store/authStore';
import { toast } from 'sonner';
import HeartCursor from '@/components/HeartCursor';
import {
  getSocket,
  callUser,
  answerCall,
  rejectCall,
  endCall as socketEndCall,
  sendIceCandidate,
  onCallAnswered,
  onCallRejected,
  onCallEnded,
  onIceCandidate,
  removeCallListeners,
} from '@/services/socket';

const ICE_SERVERS = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
};

const CallPage = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const callType = searchParams.get('type') || 'audio';
  const isIncoming = searchParams.get('incoming') === 'true';
  const incomingOffer = searchParams.get('offer');
  const incomingCallId = searchParams.get('callId');
  
  const { user, refreshCredits } = useAuthStore();
  
  const [callStatus, setCallStatus] = useState(isIncoming ? 'incoming' : 'connecting');
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(callType === 'audio');
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [coinsUsed, setCoinsUsed] = useState(0);
  const [currentCallId, setCurrentCallId] = useState(incomingCallId || null);
  
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const localStreamRef = useRef(null);
  const timerRef = useRef(null);
  const coinDeductionRef = useRef(null);
  const callIdRef = useRef(incomingCallId || null);
  const timerStartedRef = useRef(false);

  const AUDIO_COST_PER_MIN = 5;
  const VIDEO_COST_PER_MIN = 10;
  const currentCostPerMin = callType === 'video' ? VIDEO_COST_PER_MIN : AUDIO_COST_PER_MIN;

  const setupMediaStream = useCallback(async () => {
    try {
      const constraints = {
        audio: true,
        video: callType === 'video',
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      localStreamRef.current = stream;
      
      if (localVideoRef.current && callType === 'video') {
        localVideoRef.current.srcObject = stream;
      }
      
      return stream;
    } catch (error) {
      console.error('Error accessing media devices:', error);
      toast.error('Could not access camera/microphone');
      return null;
    }
  }, [callType]);

  const createPeerConnection = useCallback((callIdValue) => {
    const pc = new RTCPeerConnection(ICE_SERVERS);
    
    pc.onicecandidate = (event) => {
      const cid = callIdRef.current;
      if (event.candidate && cid) {
        sendIceCandidate(cid, event.candidate);
      }
    };
    
    pc.ontrack = (event) => {
      if (remoteVideoRef.current) {
        remoteVideoRef.current.srcObject = event.streams[0];
      }
    };
    
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === 'connected') {
        setCallStatus('connected');
        if (!timerStartedRef.current) {
          timerStartedRef.current = true;
          startCallTimer();
        }
      } else if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
        cleanup();
        navigate('/dashboard/chat');
      }
    };
    
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => {
        pc.addTrack(track, localStreamRef.current);
      });
    }
    
    peerConnectionRef.current = pc;
    return pc;
  }, []);

  const initiateCall = useCallback(async () => {
    const stream = await setupMediaStream();
    if (!stream) return;
    
    const pc = createPeerConnection(null);
    
    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      
      const response = await callUser(userId, callType, offer);
      if (response.success) {
        setCurrentCallId(response.call_id);
        callIdRef.current = response.call_id;
        setCallStatus('ringing');
      }
    } catch (error) {
      console.error('Error initiating call:', error);
      toast.error('Failed to initiate call');
      cleanup();
      navigate('/dashboard/chat');
    }
  }, [userId, callType, setupMediaStream, createPeerConnection, navigate]);

  const handleIncomingCall = useCallback(async () => {
    const stream = await setupMediaStream();
    if (!stream) return;
    
    const pc = createPeerConnection(incomingCallId);
    
    try {
      if (incomingOffer) {
        const offer = JSON.parse(decodeURIComponent(incomingOffer));
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
      }
    } catch (error) {
      console.error('Error setting remote description:', error);
    }
  }, [setupMediaStream, createPeerConnection, incomingOffer, incomingCallId]);

  const acceptCall = useCallback(async () => {
    if (!peerConnectionRef.current || !callIdRef.current) return;
    
    try {
      const answer = await peerConnectionRef.current.createAnswer();
      await peerConnectionRef.current.setLocalDescription(answer);
      
      await answerCall(callIdRef.current, answer);
      setCallStatus('connecting');
    } catch (error) {
      console.error('Error accepting call:', error);
      toast.error('Failed to accept call');
    }
  }, []);

  const handleRejectCall = useCallback(async () => {
    if (callIdRef.current) {
      try {
        await rejectCall(callIdRef.current, 'rejected');
      } catch (error) {
        console.error('Error rejecting call:', error);
      }
    }
    cleanup();
    navigate('/dashboard/chat');
  }, [navigate]);

  const startCallTimer = () => {
    timerRef.current = setInterval(() => {
      setCallDuration((prev) => prev + 1);
    }, 1000);

    coinDeductionRef.current = setInterval(() => {
      setCoinsUsed((prev) => prev + currentCostPerMin);
      toast.info(`-${currentCostPerMin} coins (${callType} call)`);
    }, 60000);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const cleanup = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (coinDeductionRef.current) clearInterval(coinDeductionRef.current);
    
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => track.stop());
      localStreamRef.current = null;
    }
    
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    removeCallListeners();
  }, []);

  const handleEndCall = useCallback(async () => {
    const cid = callIdRef.current;
    const duration = callDuration;
    
    cleanup();
    
    if (cid) {
      try {
        await socketEndCall(cid);
      } catch (error) {
        console.error('Error ending call:', error);
      }
    }
    
    const partialMinutes = Math.ceil(duration / 60);
    const totalCost = partialMinutes * currentCostPerMin;
    
    if (duration > 0) {
      toast.success(`Call ended. Total: ${totalCost} coins for ${formatDuration(duration)}`);
    }
    
    refreshCredits();
    navigate('/dashboard/chat');
  }, [callDuration, currentCostPerMin, cleanup, refreshCredits, navigate]);

  const toggleMute = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = isMuted;
      });
      setIsMuted(!isMuted);
    }
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach((track) => {
        track.enabled = isVideoOff;
      });
      setIsVideoOff(!isVideoOff);
    }
  };

  useEffect(() => {
    if ((user?.credits_balance || 0) < currentCostPerMin) {
      toast.error(`You need at least ${currentCostPerMin} coins to start a ${callType} call`);
      navigate('/dashboard/credits');
      return;
    }
    
    const socket = getSocket();
    if (!socket?.connected) {
      toast.error('Not connected to server');
      navigate('/dashboard/chat');
      return;
    }

    if (isIncoming) {
      handleIncomingCall();
    } else {
      initiateCall();
    }

    onCallAnswered(async (data) => {
      const cid = callIdRef.current;
      if (data.call_id === cid && peerConnectionRef.current && data.answer) {
        try {
          await peerConnectionRef.current.setRemoteDescription(
            new RTCSessionDescription(data.answer)
          );
          setCallStatus('connected');
          if (!timerStartedRef.current) {
            timerStartedRef.current = true;
            startCallTimer();
          }
        } catch (error) {
          console.error('Error setting remote answer:', error);
        }
      }
    });

    onCallRejected((data) => {
      const cid = callIdRef.current;
      if (data.call_id === cid) {
        toast.error('Call was rejected');
        cleanup();
        navigate('/dashboard/chat');
      }
    });

    onCallEnded((data) => {
      const cid = callIdRef.current;
      if (data.call_id === cid) {
        toast.info('Call ended by other user');
        cleanup();
        navigate('/dashboard/chat');
      }
    });

    onIceCandidate(async (data) => {
      const cid = callIdRef.current;
      if (data.call_id === cid && peerConnectionRef.current && data.candidate) {
        try {
          await peerConnectionRef.current.addIceCandidate(
            new RTCIceCandidate(data.candidate)
          );
        } catch (error) {
          console.error('Error adding ICE candidate:', error);
        }
      }
    });

    return () => {
      cleanup();
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0F172A] to-[#1E293B] flex flex-col items-center justify-center lg:cursor-none">
      <HeartCursor />
      {callType === 'video' && (
        <video
          ref={remoteVideoRef}
          autoPlay
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
      
      <div className="relative z-10 text-center mb-8">
        <div className="w-32 h-32 rounded-full bg-[#E9D5FF] mx-auto mb-4 flex items-center justify-center overflow-hidden">
          <span className="text-5xl text-[#0F172A]">U</span>
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">User</h2>
        
        {callStatus === 'incoming' && (
          <div className="text-gray-400">
            <p className="text-lg mb-4">Incoming {callType} call...</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleRejectCall}
                className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center"
              >
                <PhoneOff size={28} className="text-white" />
              </button>
              <button
                onClick={acceptCall}
                className="w-16 h-16 rounded-full bg-green-500 flex items-center justify-center"
              >
                <Phone size={28} className="text-white" />
              </button>
            </div>
          </div>
        )}
        
        {callStatus === 'connecting' && (
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Connecting...</span>
          </div>
        )}
        
        {callStatus === 'ringing' && (
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <Phone className="w-4 h-4 animate-pulse" />
            <span>Ringing...</span>
          </div>
        )}
        
        {callStatus === 'connected' && (
          <div className="text-gray-400">
            <p className="text-2xl font-mono mb-1">{formatDuration(callDuration)}</p>
            <p className="text-sm flex items-center justify-center gap-1">
              <Coins size={14} />
              {currentCostPerMin} coins/min
            </p>
          </div>
        )}
      </div>

      {callType === 'video' && !isVideoOff && (
        <div className="absolute top-4 right-4 w-32 h-44 bg-gray-800 rounded-2xl overflow-hidden shadow-xl z-20">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {callStatus !== 'incoming' && (
        <div className="relative z-10 flex items-center gap-4">
          <button
            onClick={toggleMute}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
              isMuted ? 'bg-red-500' : 'bg-white/20'
            }`}
          >
            {isMuted ? <MicOff size={24} className="text-white" /> : <Mic size={24} className="text-white" />}
          </button>

          {callType === 'video' && (
            <button
              onClick={toggleVideo}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
                isVideoOff ? 'bg-red-500' : 'bg-white/20'
              }`}
            >
              {isVideoOff ? <VideoOff size={24} className="text-white" /> : <Video size={24} className="text-white" />}
            </button>
          )}

          <button
            onClick={handleEndCall}
            className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors"
          >
            <PhoneOff size={28} className="text-white" />
          </button>

          <button
            onClick={() => setIsSpeakerOn(!isSpeakerOn)}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
              !isSpeakerOn ? 'bg-red-500' : 'bg-white/20'
            }`}
          >
            {isSpeakerOn ? <Volume2 size={24} className="text-white" /> : <VolumeX size={24} className="text-white" />}
          </button>
        </div>
      )}

      <div className="absolute bottom-8 left-0 right-0 text-center z-10">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-2">
          <Coins size={18} className="text-yellow-400" />
          <span className="text-white">Balance: {(user?.credits_balance || 0) - coinsUsed} coins</span>
        </div>
      </div>
    </div>
  );
};

export default CallPage;
