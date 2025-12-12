import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight } from 'lucide-react';

const introImages = [
  {
    url: 'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/szubcfsh_0f9404175493827.64b512011929a.jpg',
    bgColor: 'from-pink-400 via-pink-500 to-blue-500',
    overlayColor: 'rgba(236, 72, 153, 0.3)',
  },
  {
    url: 'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/i7v9p713_3d3d2a175493827.64b51201182d8.jpg',
    bgColor: 'from-blue-500 via-blue-600 to-indigo-600',
    overlayColor: 'rgba(59, 130, 246, 0.3)',
  },
  {
    url: 'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/m35haapv_21e4fe175493827.64b572b9e145b.jpg',
    bgColor: 'from-cyan-400 via-teal-500 to-blue-600',
    overlayColor: 'rgba(6, 182, 212, 0.3)',
  },
  {
    url: 'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/vvcj2l4m_b99991175493827.64b512011a181.jpg',
    bgColor: 'from-pink-500 via-fuchsia-500 to-purple-500',
    overlayColor: 'rgba(236, 72, 153, 0.3)',
  },
  {
    url: 'https://customer-assets.emergentagent.com/job_pairly-comms/artifacts/r4v2oh1b_ca35f1192469755.Y3JvcCwxNjgzLDEzMTYsMCww.jpg',
    bgColor: 'from-slate-900 via-purple-900 to-slate-900',
    overlayColor: 'rgba(15, 23, 42, 0.3)',
  },
];

const IntroSlides = () => {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [touchStart, setTouchStart] = useState(null);
  const [imagesLoaded, setImagesLoaded] = useState(false);

  // Preload images
  useEffect(() => {
    const preloadImages = async () => {
      const promises = introImages.map((img) => {
        return new Promise((resolve) => {
          const image = new Image();
          image.src = img.url;
          image.onload = resolve;
          image.onerror = resolve;
        });
      });
      await Promise.all(promises);
      setImagesLoaded(true);
    };
    preloadImages();
  }, []);

  const goToNextSlide = useCallback(() => {
    if (isTransitioning) return;
    
    if (currentSlide === introImages.length - 1) {
      // Last slide, go to login
      setIsTransitioning(true);
      setTimeout(() => {
        navigate('/login');
      }, 500);
    } else {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentSlide(currentSlide + 1);
        setIsTransitioning(false);
      }, 300);
    }
  }, [currentSlide, isTransitioning, navigate]);

  const goToPrevSlide = useCallback(() => {
    if (isTransitioning || currentSlide === 0) return;
    
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentSlide(currentSlide - 1);
      setIsTransitioning(false);
    }, 300);
  }, [currentSlide, isTransitioning]);

  // Handle scroll
  useEffect(() => {
    const handleWheel = (e) => {
      if (e.deltaY > 0) {
        goToNextSlide();
      } else if (e.deltaY < 0) {
        goToPrevSlide();
      }
    };

    window.addEventListener('wheel', handleWheel, { passive: true });
    return () => window.removeEventListener('wheel', handleWheel);
  }, [goToNextSlide, goToPrevSlide]);

  // Handle keyboard
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        goToNextSlide();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        goToPrevSlide();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToNextSlide, goToPrevSlide]);

  // Handle touch
  const handleTouchStart = (e) => {
    setTouchStart(e.touches[0].clientY);
  };

  const handleTouchEnd = (e) => {
    if (touchStart === null) return;
    
    const touchEnd = e.changedTouches[0].clientY;
    const diff = touchStart - touchEnd;
    
    if (diff > 50) {
      goToNextSlide();
    } else if (diff < -50) {
      goToPrevSlide();
    }
    
    setTouchStart(null);
  };

  const skipToLogin = () => {
    navigate('/login');
  };

  if (!imagesLoaded) {
    return (
      <div className="fixed inset-0 bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  const currentImage = introImages[currentSlide];

  return (
    <div 
      className="fixed inset-0 overflow-hidden"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Background gradient */}
      <div 
        className={`absolute inset-0 bg-gradient-to-br ${currentImage.bgColor} transition-all duration-700`}
      />

      {/* Image container */}
      <div className="absolute inset-0 flex items-center justify-center p-8">
        <div 
          className={`relative transition-all duration-500 ease-out ${
            isTransitioning ? 'opacity-0 translate-y-8' : 'opacity-100 translate-y-0'
          }`}
        >
          {/* Glow effect */}
          <div 
            className="absolute -inset-8 rounded-3xl blur-3xl opacity-50"
            style={{ backgroundColor: currentImage.overlayColor }}
          />
          
          {/* Image */}
          <img
            src={currentImage.url}
            alt={`Intro ${currentSlide + 1}`}
            className="relative max-w-full max-h-[70vh] w-auto h-auto object-contain rounded-2xl shadow-2xl"
            style={{
              boxShadow: `0 25px 100px -20px ${currentImage.overlayColor}, 0 0 60px -15px ${currentImage.overlayColor}`,
            }}
          />
        </div>
      </div>

      {/* Progress indicators */}
      <div className="absolute bottom-24 left-1/2 -translate-x-1/2 flex gap-2">
        {introImages.map((_, index) => (
          <button
            key={index}
            onClick={() => {
              if (!isTransitioning) {
                setIsTransitioning(true);
                setTimeout(() => {
                  setCurrentSlide(index);
                  setIsTransitioning(false);
                }, 300);
              }
            }}
            className={`h-2 rounded-full transition-all duration-300 ${
              index === currentSlide 
                ? 'w-8 bg-white' 
                : 'w-2 bg-white/40 hover:bg-white/60'
            }`}
          />
        ))}
      </div>

      {/* Navigation hints */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
        <p className="text-white/60 text-sm">
          {currentSlide === introImages.length - 1 ? 'Tap to continue' : 'Scroll or swipe to continue'}
        </p>
        <button
          onClick={goToNextSlide}
          className="animate-bounce"
        >
          {currentSlide === introImages.length - 1 ? (
            <ChevronRight className="h-6 w-6 text-white/80" />
          ) : (
            <ChevronDown className="h-6 w-6 text-white/80" />
          )}
        </button>
      </div>

      {/* Skip button */}
      <button
        onClick={skipToLogin}
        className="absolute top-6 right-6 px-4 py-2 text-white/80 hover:text-white text-sm font-medium transition-colors"
      >
        Skip
      </button>

      {/* Slide counter */}
      <div className="absolute top-6 left-6 text-white/60 text-sm font-medium">
        {currentSlide + 1} / {introImages.length}
      </div>
    </div>
  );
};

export default IntroSlides;
