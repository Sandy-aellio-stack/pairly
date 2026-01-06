import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';

const HeartCursor = () => {
  const cursorRef = useRef(null);
  const trailRef = useRef(null);
  const [isHovering, setIsHovering] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const [isMobile, setIsMobile] = useState(true);

  useEffect(() => {
    const checkMobile = () => {
      const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      const isSmallScreen = window.innerWidth < 1024;
      setIsMobile(isTouch || isSmallScreen);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  useEffect(() => {
    if (isMobile) return;
    
    const styleId = 'heart-cursor-style';
    let style = document.getElementById(styleId);
    if (!style) {
      style = document.createElement('style');
      style.id = styleId;
      style.textContent = `
        @media (min-width: 1024px) {
          *, *::before, *::after {
            cursor: none !important;
          }
        }
      `;
      document.head.appendChild(style);
    }
    
    return () => {
      const existingStyle = document.getElementById(styleId);
      if (existingStyle) {
        existingStyle.remove();
      }
    };
  }, [isMobile]);

  useEffect(() => {
    if (isMobile) return;
    
    const cursor = cursorRef.current;
    const trail = trailRef.current;
    
    if (!cursor || !trail) return;

    // Initial position off-screen using left/top for reliable fixed positioning
    gsap.set(cursor, { left: -100, top: -100 });
    gsap.set(trail, { left: -100, top: -100 });

    const onMouseMove = (e) => {
      // Use clientX/clientY for viewport-relative positioning with fixed elements
      const x = e.clientX;
      const y = e.clientY;
      
      // Main cursor - follows quickly using left/top
      gsap.to(cursor, {
        left: x,
        top: y,
        duration: 0.1,
        ease: 'none',
      });
      
      // Trail - follows with slight delay for smooth effect
      gsap.to(trail, {
        left: x,
        top: y,
        duration: 0.3,
        ease: 'power2.out',
      });
    };

    const onMouseDown = () => {
      setIsClicking(true);
      gsap.to(cursor, { scale: 0.7, duration: 0.1 });
      gsap.to(trail, { scale: 1.5, opacity: 0.3, duration: 0.1 });
    };

    const onMouseUp = () => {
      setIsClicking(false);
      gsap.to(cursor, { scale: 1, duration: 0.2, ease: 'elastic.out(1, 0.5)' });
      gsap.to(trail, { scale: 1, opacity: 0.5, duration: 0.2 });
    };

    const onMouseEnter = () => {
      gsap.to(cursor, { opacity: 1, scale: 1, duration: 0.3 });
      gsap.to(trail, { opacity: 0.5, duration: 0.3 });
    };

    const onMouseLeave = () => {
      gsap.to(cursor, { opacity: 0, duration: 0.3 });
      gsap.to(trail, { opacity: 0, duration: 0.3 });
    };

    // Handle hover on interactive elements using event delegation
    const onMouseOver = (e) => {
      const target = e.target;
      if (target.matches('button, a, input, textarea, select, [role="button"], .clickable')) {
        setIsHovering(true);
        gsap.to(cursor, { scale: 1.4, duration: 0.2 });
        gsap.to(trail, { scale: 2, opacity: 0.2, duration: 0.3 });
      }
    };

    const onMouseOut = (e) => {
      const target = e.target;
      if (target.matches('button, a, input, textarea, select, [role="button"], .clickable')) {
        setIsHovering(false);
        gsap.to(cursor, { scale: 1, duration: 0.2 });
        gsap.to(trail, { scale: 1, opacity: 0.5, duration: 0.3 });
      }
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseenter', onMouseEnter);
    document.addEventListener('mouseleave', onMouseLeave);
    document.addEventListener('mouseover', onMouseOver);
    document.addEventListener('mouseout', onMouseOut);

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mouseenter', onMouseEnter);
      document.removeEventListener('mouseleave', onMouseLeave);
      document.removeEventListener('mouseover', onMouseOver);
      document.removeEventListener('mouseout', onMouseOut);
    };
  }, [isMobile]);

  return (
    <>
      {/* Trail/Glow effect */}
      <div
        ref={trailRef}
        className="fixed pointer-events-none z-[9998] hidden lg:block mix-blend-screen"
        style={{
          width: '40px',
          height: '40px',
          transform: 'translate(-50%, -50%)',
          background: 'radial-gradient(circle, rgba(244, 114, 182, 0.6) 0%, rgba(244, 114, 182, 0) 70%)',
          borderRadius: '50%',
          filter: 'blur(4px)',
        }}
      />
      
      {/* Main heart cursor */}
      <div
        ref={cursorRef}
        className="fixed pointer-events-none z-[9999] hidden lg:block"
        style={{
          transform: 'translate(-50%, -50%)',
        }}
      >
        <svg 
          width="32" 
          height="32" 
          viewBox="0 0 32 32" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
          className={`transition-all duration-100 ${isHovering ? 'drop-shadow-lg' : ''}`}
        >
          {/* Outer glow */}
          <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <linearGradient id="heartGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F472B6" />
              <stop offset="50%" stopColor="#EC4899" />
              <stop offset="100%" stopColor="#DB2777" />
            </linearGradient>
          </defs>
          
          {/* Heart shape */}
          <path
            d="M16 28l-1.93-1.76C6.4 19.36 2 15.28 2 10.5 2 6.42 5.42 3 9.5 3c2.32 0 4.55 1.08 6 2.79C16.95 4.08 19.18 3 21.5 3 25.58 3 29 6.42 29 10.5c0 4.78-4.4 8.86-12.07 15.75L16 28z"
            fill="url(#heartGradient)"
            filter={isHovering ? 'url(#glow)' : ''}
            className="transition-all duration-200"
          />
          
          {/* Inner highlight */}
          <path
            d="M16 24l-1.35-1.23C8.6 17.2 5.5 14.2 5.5 10.5c0-2.76 2.24-5 5-5 1.62 0 3.18.75 4.2 1.95L16 8.9l1.3-1.45C18.32 6.25 19.88 5.5 21.5 5.5c2.76 0 5 2.24 5 5 0 3.7-3.1 6.7-9.15 12.27L16 24z"
            fill="rgba(255,255,255,0.3)"
          />
          
          {/* Center sparkle when hovering */}
          {isHovering && (
            <circle 
              cx="16" 
              cy="12" 
              r="3" 
              fill="white" 
              opacity="0.8"
              className="animate-pulse"
            />
          )}
        </svg>
        
        {/* Click ripple effect */}
        {isClicking && (
          <div 
            className="absolute inset-0 flex items-center justify-center"
            style={{ marginLeft: '16px', marginTop: '16px' }}
          >
            <div className="w-8 h-8 border-2 border-pink-400 rounded-full animate-ping opacity-50" />
          </div>
        )}
      </div>
    </>
  );
};

export default HeartCursor;
