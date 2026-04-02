import { useState, useEffect, useRef, useCallback } from 'react';
import { Phone, PhoneOff, Video, VideoOff, Mic, MicOff, Volume2, VolumeX, Loader2, Coins } from 'lucide-react';
import { useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';
import useAuthStore from '../../store/authStore';
import { toast } from 'sonner';
import {
  getSocket,
  callUser,
  answerCall,
  rejectCall,
  endCall,
  sendIceCandidate,
  onIncomingCall,
  onCallAnswered,
  onCallRejected,
  onCallEnded,
  onIceCandidate,
  sendMediaState,
  onMediaStateChange
} from '../../services/socket';

const ICE_SERVERS = {
  iceServers: [
    // Google STUN servers (free, reliable)
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'stun:stun2.l.google.com:19302' },
    { urls: 'stun:stun3.l.google.com:19302' },
    { urls: 'stun:stun4.l.google.com:19302' },
    
    // Production TURN servers (replace with your own)
    // These are example TURN servers - replace with your own credentials
    {
      urls: 'turn:turn.your-server.com:3478',
      username: import.meta.env.VITE_TURN_USERNAME || 'turnuser',
      credential: import.meta.env.VITE_TURN_CREDENTIAL || 'turnpass'
    },
    
    // Fallback TURN servers (for testing)
    {
      urls: 'turn:openrelay.metered.ca:80',
      username: 'openrelayproject',
      credential: 'openrelayproject'
    },
    {
      urls: 'turn:openrelay.metered.ca:443',
      username: 'openrelayproject',
      credential: 'openrelayproject'
    }
  ],
  iceCandidatePoolSize: 10,
  iceTransportPolicy: 'all'
};

const CallPage = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const callType = searchParams.get('type') || 'audio';
  const isIncoming = searchParams.get('incoming') === 'true';
  const incomingOffer = location.state?.offer || searchParams.get('offer');
  const incomingCallId = searchParams.get('callId');
  
  const { user, refreshUser } = useAuthStore();
  
  const [callStatus, setCallStatus] = useState(isIncoming ? 'incoming' : 'connecting');
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(callType === 'audio');
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [coinsUsed, setCoinsUsed] = useState(0);
  const [currentCallId, setCurrentCallId] = useState(incomingCallId || null);
  const [remoteVideoEnabled, setRemoteVideoEnabled] = useState(true);
  const [remoteAudioEnabled, setRemoteAudioEnabled] = useState(true);
  
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
      
      // Send call request WITH offer SDP so callee can set remote description
      const response = await callUser(userId, callType, offer);
      const cid = response?.call_id || null;
      setCurrentCallId(cid);
      callIdRef.current = cid;
      setCallStatus('ringing');
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
        let offer = incomingOffer;
        if (typeof offer === 'string') {
          try {
            offer = JSON.parse(decodeURIComponent(offer));
          } catch (e) {
            offer = JSON.parse(offer);
          }
        }
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
    
  }, []);

  const handleEndCall = useCallback(async () => {
    const cid = callIdRef.current;
    const duration = callDuration;
    
    cleanup();
    
    if (cid) {
      try {
        await endCall(cid);
      } catch (error) {
        console.error('Error ending call:', error);
      }
    }
    
    const partialMinutes = Math.ceil(duration / 60);
    const totalCost = partialMinutes * currentCostPerMin;
    
    if (duration > 0) {
      toast.success(`Call ended. Total: ${totalCost} coins for ${formatDuration(duration)}`);
    }
    
    refreshUser();
    
    // Get previous conversation from location state or navigate to chat
    const state = location.state;
    if (state?.conversationId) {
      const userName = state.userName || 'Unknown User';
      navigate(`/dashboard/chat/${state.conversationId}?user=${encodeURIComponent(userName)}&userId=${userId}`);
    } else {
      navigate('/dashboard/chat');
    }
  }, [callDuration, currentCostPerMin, cleanup, refreshUser, navigate, location.state]);

  const toggleMute = () => {
    if (localStreamRef.current) {
      const newState = !isMuted;
      localStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = isMuted; // if previously muted (isMuted=true), now enabled=true
      });
      setIsMuted(newState);
      
      // Signaling: Tell other side about mic state
      if (callIdRef.current) {
        sendMediaState(callIdRef.current, 'audio', !newState);
      }
    }
  };

  const toggleVideo = () => {
    if (localStreamRef.current) {
      const newState = !isVideoOff;
      console.log(`[CALL DEBUG] Toggling video ${newState ? 'OFF' : 'ON'}`);
      localStreamRef.current.getVideoTracks().forEach((track) => {
        track.enabled = isVideoOff; // enabled = !isVideoOff
      });
      setIsVideoOff(newState);

      // Signaling: Tell other side about camera state
      if (callIdRef.current) {
        sendMediaState(callIdRef.current, 'video', !newState);
      }
    }
  };

  // Callback ref for more robust srcObject attachment
  const setLocalVideoRef = useCallback((node) => {
    if (node && localStreamRef.current) {
      console.log('[CALL DEBUG] localVideo element mounted, attaching stream');
      node.srcObject = localStreamRef.current;
      node.play().catch(e => console.error('[CALL DEBUG] Play failed:', e));
    }
    localVideoRef.current = node;
  }, []);

  useEffect(() => {
    if ((user?.coins || 0) < currentCostPerMin) {
      toast.error(`You need at least ${currentCostPerMin} coins to start a ${callType} call`);
      navigate('/dashboard/credits');
      return;
    }

    let connectionTimeoutId = null;

    const registerListeners = () => {
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

      onMediaStateChange((data) => {
        const cid = callIdRef.current;
        if (data.call_id === cid && data.user_id !== user?.id) {
          if (data.type === 'video') setRemoteVideoEnabled(data.enabled);
          else if (data.type === 'audio') setRemoteAudioEnabled(data.enabled);
        }
      });
    };

    const socket = getSocket();
    let pendingConnectListener = null;

    if (socket?.connected) {
      registerListeners();
    } else if (socket) {
      setCallStatus('connecting');
      const onConnected = () => {
        clearTimeout(connectionTimeoutId);
        pendingConnectListener = null;
        registerListeners();
      };
      pendingConnectListener = onConnected;
      socket.once('connect', onConnected);
      connectionTimeoutId = setTimeout(() => {
        socket.off('connect', onConnected);
        pendingConnectListener = null;
        toast.error('Connection timed out — please try again');
        navigate('/dashboard/chat');
      }, 6000);
    } else {
      toast.error('Not connected to server — please try again');
      navigate('/dashboard/chat');
    }

    return () => {
      if (connectionTimeoutId) clearTimeout(connectionTimeoutId);
      if (pendingConnectListener && socket) {
        socket.off('connect', pendingConnectListener);
      }
      cleanup();
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0F172A] to-[#1E293B] flex flex-col items-center justify-center lg:cursor-none">
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
            ref={setLocalVideoRef}
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
          <span className="text-white">Balance: {(user?.coins || 0) - coinsUsed} coins</span>
        </div>
      </div>
    </div>
  );
};

export default CallPage;
