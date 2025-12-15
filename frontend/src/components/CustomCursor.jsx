import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const CustomCursor = () => {
  const cursorRef = useRef(null);
  const cursorDotRef = useRef(null);
  const cursorGlowRef = useRef(null);
  const isTouch = useRef(false);

  useEffect(() => {
    // Check for touch device
    isTouch.current = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (isTouch.current) return;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const cursor = cursorRef.current;
    const cursorDot = cursorDotRef.current;
    const cursorGlow = cursorGlowRef.current;

    let mouseX = 0;
    let mouseY = 0;
    let cursorX = 0;
    let cursorY = 0;

    const onMouseMove = (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    };

    const animate = () => {
      // Smooth lerp follow
      cursorX += (mouseX - cursorX) * 0.15;
      cursorY += (mouseY - cursorY) * 0.15;

      gsap.set(cursor, { x: cursorX - 20, y: cursorY - 20 });
      gsap.set(cursorDot, { x: cursorX - 4, y: cursorY - 4 });
      gsap.set(cursorGlow, { x: cursorX - 30, y: cursorY - 30 });

      requestAnimationFrame(animate);
    };

    // Interactive element handlers
    const onMouseEnterInteractive = () => {
      gsap.to(cursor, {
        scale: 1.5,
        borderColor: '#7B5CFF',
        duration: 0.3,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.6,
        scale: 1.3,
        duration: 0.3,
      });
    };

    const onMouseLeaveInteractive = () => {
      gsap.to(cursor, {
        scale: 1,
        borderColor: 'rgba(255, 255, 255, 0.8)',
        duration: 0.3,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.3,
        scale: 1,
        duration: 0.3,
      });
    };

    // Card/profile hover - magnify effect
    const onMouseEnterCard = () => {
      gsap.to(cursor, {
        scale: 2,
        borderColor: '#7B5CFF',
        rotation: 15,
        duration: 0.4,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.8,
        scale: 1.5,
        duration: 0.4,
      });
    };

    const onMouseLeaveCard = () => {
      gsap.to(cursor, {
        scale: 1,
        borderColor: 'rgba(255, 255, 255, 0.8)',
        rotation: 0,
        duration: 0.4,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.3,
        scale: 1,
        duration: 0.4,
      });
    };

    window.addEventListener('mousemove', onMouseMove);
    animate();

    // Add listeners to interactive elements
    const addListeners = () => {
      document.querySelectorAll('button, a, input, .interactive').forEach((el) => {
        el.addEventListener('mouseenter', onMouseEnterInteractive);
        el.addEventListener('mouseleave', onMouseLeaveInteractive);
      });

      document.querySelectorAll('.user-card, .profile-card, .map-marker').forEach((el) => {
        el.addEventListener('mouseenter', onMouseEnterCard);
        el.addEventListener('mouseleave', onMouseLeaveCard);
      });
    };

    // Initial setup and mutation observer for dynamic content
    addListeners();
    const observer = new MutationObserver(addListeners);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      observer.disconnect();
    };
  }, []);

  // Don't render on touch devices
  if (typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)) {
    return null;
  }

  return (
    <>
      {/* Main magnifying glass circle */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 w-10 h-10 pointer-events-none z-[9999] mix-blend-difference"
        style={{
          border: '2px solid rgba(255, 255, 255, 0.8)',
          borderRadius: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      >
        {/* Handle of magnifying glass */}
        <div
          className="absolute bottom-[-8px] right-[-8px] w-4 h-1 bg-white/80 rounded-full"
          style={{ transform: 'rotate(45deg)' }}
        />
      </div>

      {/* Center dot */}
      <div
        ref={cursorDotRef}
        className="fixed top-0 left-0 w-2 h-2 bg-purple-500 rounded-full pointer-events-none z-[9999]"
        style={{ transform: 'translate(-50%, -50%)' }}
      />

      {/* Purple glow */}
      <div
        ref={cursorGlowRef}
        className="fixed top-0 left-0 w-16 h-16 pointer-events-none z-[9998] opacity-30"
        style={{
          background: 'radial-gradient(circle, rgba(123, 92, 255, 0.6) 0%, transparent 70%)',
          transform: 'translate(-50%, -50%)',
          filter: 'blur(8px)',
        }}
      />
    </>
  );
};

export default CustomCursor;
