"""
Luveloop WebRTC Configuration
Production-ready WebRTC setup for audio/video calls
"""

# WebRTC Configuration for Frontend
# This configuration should be used in React/React Native applications

# Standard STUN/TURN servers configuration
WEBRTC_CONFIG = {
    "iceServers": [
        # Google STUN server (free)
        {
            "urls": "stun:stun.l.google.com:19302"
        },
        # Additional STUN servers for redundancy
        {
            "urls": "stun:stun1.l.google.com:19302"
        },
        {
            "urls": "stun:stun2.l.google.com:19302"
        },
        # TURN server configuration (required for NAT traversal)
        # Replace with your TURN server credentials
        {
            "urls": "turn:your-turn-server.com:3478",
            "username": "your-turn-username",
            "credential": "your-turn-password"
        },
        # TURN over TCP (fallback for restrictive networks)
        {
            "urls": "turn:your-turn-server.com:3478?transport=tcp",
            "username": "your-turn-username", 
            "credential": "your-turn-password"
        }
    ],
    "iceCandidatePoolSize": 10,
    "iceTransportPolicy": "all"  # Use "relay" for TURN-only mode
}

# Example TURN server setup using coturn
# Install: apt-get install coturn
# Config: /etc/turnserver.conf

"""
# coturn configuration example
# /etc/turnserver.conf

# TURN server configuration
listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0

# Authentication
use-auth-secret
static-auth-secret=your-secret-key-here
realm=luveloop

# STUN/TURN servers
server-name=turn.yourdomain.com
total-quota=100
user-quota=12
max-bps=64000

# SSL/TLS certificates (for TURN over TLS)
cert=/path/to/ssl/cert.pem
pkey=/path/to/ssl/private.key

# Logging
log-file=/var/log/turnserver.log
verbose

# Network configuration
no-multicast-peers
no-cli
no-tlsv1
no-tlsv1_1
"""

# Frontend implementation example
"""
import { io } from 'socket.io-client'

class WebRTCManager {
    constructor(socket, config = WEBRTC_CONFIG) {
        this.socket = socket
        this.config = config
        this.peerConnection = null
        this.localStream = null
        this.remoteStream = null
        this.callType = null // 'audio' or 'video'
    }

    async initiateCall(receiverId, callType = 'audio') {
        try {
            this.callType = callType
            
            // Get local media stream
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: callType === 'video',
                audio: true
            })

            // Create peer connection
            this.peerConnection = new RTCPeerConnection(this.config)
            
            // Add local stream
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream)
            })

            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    this.socket.emit('webrtc:ice-candidate', {
                        call_id: this.callId,
                        candidate: event.candidate
                    })
                }
            }

            // Handle remote stream
            this.peerConnection.ontrack = (event) => {
                this.remoteStream = event.streams[0]
                this.onRemoteStream(this.remoteStream)
            }

            // Create offer
            const offer = await this.peerConnection.createOffer()
            await this.peerConnection.setLocalDescription(offer)

            // Initiate call via socket
            const response = await this.socket.emit('call:initiate', {
                targetUserId: receiverId,
                call_type: callType,
                offer: offer
            })

            this.callId = response.call_id
            return response

        } catch (error) {
            console.error('Failed to initiate call:', error)
            throw error
        }
    }

    async handleIncomingCall(callData) {
        this.callId = callData.call_id
        this.callType = callData.call_type

        // Get local media stream
        this.localStream = await navigator.mediaDevices.getUserMedia({
            video: this.callType === 'video',
            audio: true
        })

        // Create peer connection
        this.peerConnection = new RTCPeerConnection(this.config)
        
        // Add local stream
        this.localStream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, this.localStream)
        })

        // Handle ICE candidates
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.emit('webrtc:ice-candidate', {
                    call_id: this.callId,
                    candidate: event.candidate
                })
            }
        }

        // Handle remote stream
        this.peerConnection.ontrack = (event) => {
            this.remoteStream = event.streams[0]
            this.onRemoteStream(this.remoteStream)
        }

        // Set remote description (offer)
        await this.peerConnection.setRemoteDescription(
            new RTCSessionDescription(callData.offer)
        )

        // Create and send answer
        const answer = await this.peerConnection.createAnswer()
        await this.peerConnection.setLocalDescription(answer)

        await this.socket.emit('call:accept', {
            call_id: this.callId,
            answer: answer
        })
    }

    async handleWebRTCOffer(offerData) {
        await this.peerConnection.setRemoteDescription(
            new RTCSessionDescription(offerData.offer)
        )
    }

    async handleWebRTCAnswer(answerData) {
        await this.peerConnection.setRemoteDescription(
            new RTCSessionDescription(answerData.answer)
        )
    }

    async handleICECandidate(candidateData) {
        await this.peerConnection.addIceCandidate(
            new RTCIceCandidate(candidateData.candidate)
        )
    }

    async endCall() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop())
        }
        
        if (this.peerConnection) {
            this.peerConnection.close()
        }

        await this.socket.emit('call:end', {
            call_id: this.callId
        })

        this.cleanup()
    }

    cleanup() {
        this.localStream = null
        this.remoteStream = null
        this.peerConnection = null
        this.callId = null
        this.callType = null
    }

    // Callbacks to be set by the UI
    onRemoteStream = (stream) => {
        console.log('Remote stream received:', stream)
    }

    onCallEnded = () => {
        console.log('Call ended')
    }
}

// Usage example:
const socket = io(SOCKET_URL, { auth: { token } })
const webrtc = new WebRTCManager(socket)

// Set up event listeners
socket.on('call:incoming', webrtc.handleIncomingCall.bind(webrtc))
socket.on('webrtc:offer', webrtc.handleWebRTCOffer.bind(webrtc))
socket.on('webrtc:answer', webrtc.handleWebRTCAnswer.bind(webrtc))
socket.on('webrtc:ice-candidate', webrtc.handleICECandidate.bind(webrtc))
socket.on('call:end', webrtc.cleanup.bind(webrtc))

// Start a call
await webrtc.initiateCall(userId, 'video')
"""

# React Native considerations
"""
For React Native, use:
- react-native-webrtc for WebRTC functionality
- react-native-permissions for camera/microphone permissions
- react-native-callkeep for native call UI
- react-native-background-job for background handling

Additional setup for React Native:
1. Install WebRTC package: npm install react-native-webrtc
2. Configure permissions in iOS/Android
3. Handle background modes for calls
4. Use native call UI for better UX
"""
