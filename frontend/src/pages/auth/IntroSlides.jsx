import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

// Image data with dominant colors for backgrounds
const introData = [
  {
    image: 'https://customer-assets.emergentagent.com/job_pairly-intro/artifacts/0sgc62vo_0f9404175493827.64b512011929a.jpg',
    bgGradient: 'from-pink-500 via-pink-400 to-blue-600',
    glowColor: 'rgba(236, 72, 153, 0.4)',
  },
  {
    image: 'https://customer-assets.emergentagent.com/job_pairly-intro/artifacts/ujfxavml_3d3d2a175493827.64b51201182d8.jpg',
    bgGradient: 'from-blue-600 via-blue-500 to-blue-700',
    glowColor: 'rgba(37, 99, 235, 0.4)',
  },
  {
    image: 'https://customer-assets.emergentagent.com/job_pairly-intro/artifacts/u69t8gqm_21e4fe175493827.64b572b9e145b.jpg',
    bgGradient: 'from-cyan-400 via-teal-400 to-cyan-500',
    glowColor: 'rgba(34, 211, 238, 0.4)',
  },
  {
    image: 'https://customer-assets.emergentagent.com/job_pairly-intro/artifacts/ytk6tqdk_b99991175493827.64b512011a181.jpg',
    bgGradient: 'from-pink-400 via-pink-500 to-pink-600',
    glowColor: 'rgba(236, 72, 153, 0.4)',
  },
  {
    image: 'https://customer-assets.emergentagent.com/job_pairly-intro/artifacts/0nphq1bd_ef2985175493827.64b512011b481.jpg',
    bgGradient: 'from-blue-600 via-blue-500 to-pink-500',
    glowColor: 'rgba(37, 99, 235, 0.4)',
  },
];

const IntroSlides = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [slideDirection, setSlideDirection] = useState('next');
  const [imagesLoaded, setImagesLoaded] = useState(new Set());
  const containerRef = useRef(null);
  const touchStartRef = useRef(null);
  const navigate = useNavigate();

  // Preload all images
  useEffect(() => {
    introData.forEach((item, index) => {
      const img = new Image();
      img.src = item.image;
      img.onload = () => {
        setImagesLoaded(prev => new Set([...prev, index]));
      };
    });
  }, []);

  const goToSlide = useCallback((targetSlide, direction = 'next') => {
    if (isAnimating) return;
    
    if (targetSlide >= introData.length) {
      // Navigate to login after last slide
      navigate('/login');
      return;
    }
    
    if (targetSlide < 0) return;
    
    setIsAnimating(true);
    setSlideDirection(direction);
    setCurrentSlide(targetSlide);
    
    setTimeout(() => {
      setIsAnimating(false);
    }, 600);
  }, [isAnimating, navigate]);

  const nextSlide = useCallback(() => {
    goToSlide(currentSlide + 1, 'next');
  }, [currentSlide, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(currentSlide - 1, 'prev');
  }, [currentSlide, goToSlide]);

  // Handle wheel/scroll events
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let lastScrollTime = 0;
    const scrollThreshold = 800; // ms between scrolls

    const handleWheel = (e) => {
      e.preventDefault();
      const now = Date.now();
      if (now - lastScrollTime < scrollThreshold) return;
      lastScrollTime = now;

      if (e.deltaY > 0) {
        nextSlide();
      } else if (e.deltaY < 0) {
        prevSlide();
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [nextSlide, prevSlide]);

  // Handle touch events for swipe
  const handleTouchStart = (e) => {
    touchStartRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    };
  };

  const handleTouchEnd = (e) => {
    if (!touchStartRef.current) return;

    const deltaX = e.changedTouches[0].clientX - touchStartRef.current.x;
    const deltaY = e.changedTouches[0].clientY - touchStartRef.current.y;
    const threshold = 50;

    // Prioritize vertical swipe
    if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > threshold) {
      if (deltaY < 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }
    // Also handle horizontal swipe
    else if (Math.abs(deltaX) > threshold) {
      if (deltaX < 0) {
        nextSlide();
      } else {
        prevSlide();
      }
    }

    touchStartRef.current = null;
  };

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        prevSlide();
      } else if (e.key === 'Escape') {
        navigate('/login');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextSlide, prevSlide, navigate]);

  const currentData = introData[currentSlide];

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 overflow-hidden touch-none"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* Animated Background */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${currentData.bgGradient} transition-all duration-700`}
      />

      {/* Image Container */}
      <div className="absolute inset-0 flex items-center justify-center">
        {introData.map((item, index) => (
          <div
            key={index}
            className={`absolute transition-all duration-600 ease-out ${
              index === currentSlide
                ? 'opacity-100 translate-y-0 scale-100'
                : index < currentSlide
                ? 'opacity-0 -translate-y-8 scale-95'
                : 'opacity-0 translate-y-8 scale-95'
            }`}
            style={{
              transitionDuration: '600ms',
              transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            {/* Soft glow behind image */}
            <div
              className="absolute inset-0 blur-3xl opacity-60 scale-110"
              style={{
                background: item.glowColor,
                borderRadius: '24px',
              }}
            />
            
            {/* Main Image */}
            <div className="relative">
              <img
                src={item.image}
                alt={`Intro ${index + 1}`}
                className="relative max-w-[85vw] max-h-[75vh] w-auto h-auto object-contain rounded-2xl shadow-2xl"
                style={{
                  boxShadow: `0 25px 80px -12px ${item.glowColor}, 0 4px 20px rgba(0,0,0,0.3)`,
                }}
                loading="eager"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Skip button */}
      <button
        onClick={() => navigate('/login')}
        className="absolute top-6 right-6 z-50 px-5 py-2.5 bg-white/20 backdrop-blur-md rounded-full text-white font-medium text-sm hover:bg-white/30 transition-all duration-200 border border-white/30"
      >
        Skip
      </button>

      {/* Progress indicators */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-50 flex gap-2">
        {introData.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index, index > currentSlide ? 'next' : 'prev')}
            className={`h-2 rounded-full transition-all duration-300 ${
              index === currentSlide
                ? 'w-8 bg-white'
                : 'w-2 bg-white/40 hover:bg-white/60'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>

      {/* Navigation arrows */}
      <div className="absolute bottom-8 right-8 z-50 flex gap-3">
        <button
          onClick={prevSlide}
          disabled={currentSlide === 0}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200 ${
            currentSlide === 0
              ? 'bg-white/10 text-white/30 cursor-not-allowed'
              : 'bg-white/20 text-white hover:bg-white/30 backdrop-blur-md border border-white/30'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </button>
        <button
          onClick={nextSlide}
          className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md text-white hover:bg-white/30 transition-all duration-200 flex items-center justify-center border border-white/30"
        >
          {currentSlide === introData.length - 1 ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </button>
      </div>

      {/* Scroll hint */}
      {currentSlide === 0 && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-50 animate-bounce">
          <div className="flex flex-col items-center gap-2 text-white/70">
            <span className="text-xs font-medium">Scroll or swipe</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntroSlides;