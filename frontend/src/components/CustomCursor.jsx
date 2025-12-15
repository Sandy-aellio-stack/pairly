import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const CustomCursor = () => {
  const cursorRef = useRef(null);
  const cursorGlowRef = useRef(null);
  const isTouch = useRef(false);

  useEffect(() => {
    isTouch.current = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (isTouch.current) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    const cursor = cursorRef.current;
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
      cursorX += (mouseX - cursorX) * 0.12;
      cursorY += (mouseY - cursorY) * 0.12;

      gsap.set(cursor, { x: cursorX - 16, y: cursorY - 16 });
      gsap.set(cursorGlow, { x: cursorX - 24, y: cursorY - 24 });

      requestAnimationFrame(animate);
    };

    const onMouseEnterInteractive = () => {
      gsap.to(cursor, {
        scale: 1.4,
        borderColor: '#7B5CFF',
        duration: 0.3,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.8,
        scale: 1.3,
        duration: 0.3,
      });
    };

    const onMouseLeaveInteractive = () => {
      gsap.to(cursor, {
        scale: 1,
        borderColor: '#7B5CFF',
        duration: 0.3,
        ease: 'power2.out',
      });
      gsap.to(cursorGlow, {
        opacity: 0.4,
        scale: 1,
        duration: 0.3,
      });
    };

    const onMouseEnterCard = () => {
      gsap.to(cursor, {
        scale: 1.8,
        rotation: 10,
        duration: 0.4,
        ease: 'power2.out',
      });
    };

    const onMouseLeaveCard = () => {
      gsap.to(cursor, {
        scale: 1,
        rotation: 0,
        duration: 0.4,
        ease: 'power2.out',
      });
    };

    window.addEventListener('mousemove', onMouseMove);
    animate();

    const addListeners = () => {
      document.querySelectorAll('button, a, input, select, textarea, .interactive').forEach((el) => {
        el.addEventListener('mouseenter', onMouseEnterInteractive);
        el.addEventListener('mouseleave', onMouseLeaveInteractive);
      });

      document.querySelectorAll('.user-card, .story-bubble, .profile-card').forEach((el) => {
        el.addEventListener('mouseenter', onMouseEnterCard);
        el.addEventListener('mouseleave', onMouseLeaveCard);
      });
    };

    addListeners();
    const observer = new MutationObserver(addListeners);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      observer.disconnect();
    };
  }, []);

  if (typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)) {
    return null;
  }

  return (
    <>
      {/* Magnifying glass */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 w-8 h-8 pointer-events-none z-[9999]"
        style={{
          border: '2px solid #7B5CFF',
          borderRadius: '50%',
        }}
      >
        {/* Handle */}
        <div
          className="absolute bottom-[-6px] right-[-6px] w-3 h-1 rounded-full"
          style={{ 
            background: '#7B5CFF',
            transform: 'rotate(45deg)' 
          }}
        />
        {/* Inner dot */}
        <div 
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full"
          style={{ background: '#7B5CFF' }}
        />
      </div>

      {/* Glow */}
      <div
        ref={cursorGlowRef}
        className="fixed top-0 left-0 w-12 h-12 pointer-events-none z-[9998] opacity-40"
        style={{
          background: 'radial-gradient(circle, rgba(123, 92, 255, 0.5) 0%, transparent 70%)',
          filter: 'blur(8px)',
        }}
      />
    </>
  );
};

export default CustomCursor;
