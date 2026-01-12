import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  MapPin, 
  MessageCircle, 
  Heart, 
  Shield, 
  Flag, 
  MoreVertical,
  Loader2,
  X,
  Check,
  Clock,
  Circle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import api from '@/services/api';
import useAuthStore from '@/store/authStore';

const ProfileViewerPage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuthStore();
  
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [showMenu, setShowMenu] = useState(false);
  const [showBlockModal, setShowBlockModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const [isBlocking, setIsBlocking] = useState(false);
  const [isReporting, setIsReporting] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  const fetchProfile = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/api/users/profile/${userId}`);
      setProfile(response.data);
    } catch (err) {
      if (err.response?.status === 403) {
        setError('This profile is not available');
      } else if (err.response?.status === 404) {
        setError('User not found');
      } else {
        setError('Failed to load profile');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    navigate(-1);
  };

  const handleMessage = () => {
    if (currentUser?.credits_balance > 0) {
      navigate(`/dashboard/chat?user=${userId}`);
    } else {
      toast.error('You need coins to send messages!');
      navigate('/dashboard/credits');
    }
  };

  const handleLike = () => {
    toast.success(`You liked ${profile?.name}!`);
  };

  const handleBlock = async () => {
    setIsBlocking(true);
    try {
      await api.post(`/api/users/block/${userId}`);
      toast.success('User blocked');
      setShowBlockModal(false);
      navigate(-1);
    } catch (err) {
      toast.error('Failed to block user');
    } finally {
      setIsBlocking(false);
    }
  };

  const handleReport = async () => {
    if (reportReason.length < 10) {
      toast.error('Please provide more details');
      return;
    }
    
    setIsReporting(true);
    try {
      await api.post(`/api/users/report/${userId}`, {
        reason: reportReason,
        report_type: 'profile'
      });
      toast.success('Report submitted. Thank you for keeping our community safe.');
      setShowReportModal(false);
      setReportReason('');
    } catch (err) {
      toast.error('Failed to submit report');
    } finally {
      setIsReporting(false);
    }
  };

  const nextPhoto = () => {
    if (profile?.profile_pictures?.length > 1) {
      setCurrentPhotoIndex((prev) => 
        prev === profile.profile_pictures.length - 1 ? 0 : prev + 1
      );
    }
  };

  const prevPhoto = () => {
    if (profile?.profile_pictures?.length > 1) {
      setCurrentPhotoIndex((prev) => 
        prev === 0 ? profile.profile_pictures.length - 1 : prev - 1
      );
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-[#0F172A] mx-auto mb-4" />
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <X className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">{error}</h2>
          <p className="text-gray-600 mb-6">This profile may have been removed or is not accessible.</p>
          <button
            onClick={handleBack}
            className="px-6 py-2 bg-[#0F172A] text-white rounded-lg hover:bg-[#1E293B] transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const photos = profile?.profile_pictures?.length > 0 
    ? profile.profile_pictures 
    : ['https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-lg border-b border-gray-100">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={handleBack}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ArrowLeft className="w-6 h-6 text-gray-700" />
          </button>
          
          <h1 className="font-semibold text-gray-900">{profile?.name}</h1>
          
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <MoreVertical className="w-6 h-6 text-gray-700" />
            </button>
            
            {/* Dropdown Menu */}
            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -10 }}
                  className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden"
                >
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      setShowBlockModal(true);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-gray-700"
                  >
                    <Shield className="w-5 h-5" />
                    Block User
                  </button>
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      setShowReportModal(true);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center gap-3 text-red-600"
                  >
                    <Flag className="w-5 h-5" />
                    Report User
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Profile Content */}
      <div className="max-w-2xl mx-auto pb-24">
        {/* Photo Gallery */}
        <div className="relative">
          <div className="aspect-[3/4] bg-gray-200">
            <img
              src={photos[currentPhotoIndex]}
              alt={profile?.name}
              className="w-full h-full object-cover"
            />
          </div>
          
          {/* Photo Navigation Dots */}
          {photos.length > 1 && (
            <div className="absolute top-4 left-0 right-0 flex justify-center gap-1.5 px-4">
              {photos.map((_, idx) => (
                <div
                  key={idx}
                  className={`h-1 rounded-full transition-all ${
                    idx === currentPhotoIndex 
                      ? 'w-8 bg-white' 
                      : 'w-1.5 bg-white/50'
                  }`}
                />
              ))}
            </div>
          )}
          
          {/* Photo Navigation Areas */}
          {photos.length > 1 && (
            <>
              <div 
                className="absolute top-0 left-0 w-1/3 h-full cursor-pointer"
                onClick={prevPhoto}
              />
              <div 
                className="absolute top-0 right-0 w-1/3 h-full cursor-pointer"
                onClick={nextPhoto}
              />
            </>
          )}
          
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
          
          {/* Profile Info Overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold">{profile?.name}, {profile?.age}</h2>
              {profile?.is_verified && (
                <div className="px-2 py-1 bg-blue-500/80 rounded-full flex items-center gap-1">
                  <Check className="w-3 h-3" />
                  <span className="text-xs">Verified</span>
                </div>
              )}
            </div>
            
            {/* Online Status */}
            <div className="flex items-center gap-4 text-sm text-white/80 mb-1">
              {profile?.is_online !== null && (
                <div className="flex items-center gap-1.5">
                  <Circle 
                    className={`w-2 h-2 ${profile.is_online ? 'text-green-400 fill-green-400' : 'text-gray-400 fill-gray-400'}`} 
                  />
                  <span>{profile.is_online ? 'Online' : profile.last_active || 'Offline'}</span>
                </div>
              )}
            </div>
            
            {/* Distance */}
            <div className="flex items-center gap-2 text-sm text-white/80">
              <MapPin className="w-4 h-4" />
              <span>{profile?.distance_display || 'Distance hidden'}</span>
              {profile?.location_fresh && (
                <span className="px-1.5 py-0.5 bg-white/20 rounded text-xs">Live</span>
              )}
            </div>
          </div>
        </div>

        {/* Profile Details */}
        <div className="bg-white px-6 py-6 space-y-6">
          {/* Intent Badge */}
          {profile?.intent && (
            <div className="flex items-center gap-2">
              <span className="px-4 py-2 bg-[#E9D5FF] text-[#0F172A] rounded-full text-sm font-medium">
                Looking for {profile.intent}
              </span>
            </div>
          )}
          
          {/* Bio */}
          {profile?.bio && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">About</h3>
              <p className="text-gray-600 leading-relaxed">{profile.bio}</p>
            </div>
          )}
          
          {/* Basic Info */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Basic Info</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm">
                  <span className="text-lg">🎂</span>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Age</p>
                  <p className="font-medium text-gray-900">{profile?.age} years</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-sm">
                  <span className="text-lg">{profile?.gender === 'male' ? '👨' : profile?.gender === 'female' ? '👩' : '🧑'}</span>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Gender</p>
                  <p className="font-medium text-gray-900 capitalize">{profile?.gender}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 px-4 py-4 safe-area-pb">
        <div className="max-w-2xl mx-auto flex items-center justify-center gap-4">
          <button
            onClick={handleMessage}
            className="flex-1 py-3 px-6 bg-[#0F172A] text-white rounded-xl font-medium hover:bg-[#1E293B] transition-colors flex items-center justify-center gap-2"
          >
            <MessageCircle className="w-5 h-5" />
            Message (1 coin)
          </button>
          
          <button
            onClick={handleLike}
            className="w-14 h-14 bg-rose-500 text-white rounded-full flex items-center justify-center hover:bg-rose-600 transition-colors shadow-lg"
          >
            <Heart className="w-6 h-6" fill="white" />
          </button>
        </div>
      </div>

      {/* Block Modal */}
      <AnimatePresence>
        {showBlockModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setShowBlockModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-sm w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-8 h-8 text-red-500" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Block {profile?.name}?</h3>
                <p className="text-gray-600 text-sm">
                  They won't be able to find your profile or send you messages. 
                  You can unblock them anytime from settings.
                </p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowBlockModal(false)}
                  className="flex-1 py-3 border border-gray-200 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBlock}
                  disabled={isBlocking}
                  className="flex-1 py-3 bg-red-500 text-white rounded-xl font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
                >
                  {isBlocking ? 'Blocking...' : 'Block'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Report Modal */}
      <AnimatePresence>
        {showReportModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={() => setShowReportModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-sm w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="mb-6">
                <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Flag className="w-8 h-8 text-orange-500" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 text-center mb-2">Report {profile?.name}</h3>
                <p className="text-gray-600 text-sm text-center">
                  Help us keep TrueBond safe. Reports are reviewed by our team.
                </p>
              </div>
              
              <textarea
                value={reportReason}
                onChange={(e) => setReportReason(e.target.value)}
                placeholder="Please describe the issue (at least 10 characters)..."
                className="w-full p-3 border border-gray-200 rounded-xl mb-4 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-[#0F172A] focus:border-transparent"
              />
              
              <div className="flex gap-3">
                <button
                  onClick={() => setShowReportModal(false)}
                  className="flex-1 py-3 border border-gray-200 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReport}
                  disabled={isReporting || reportReason.length < 10}
                  className="flex-1 py-3 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 transition-colors disabled:opacity-50"
                >
                  {isReporting ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProfileViewerPage;
