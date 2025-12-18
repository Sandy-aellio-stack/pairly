import { useEffect, useRef } from 'react';
import gsap from 'gsap';

const HeartCursor = () => {
  const cursorRef = useRef(null);
  const cursorDotRef = useRef(null);

  useEffect(() => {
    const cursor = cursorRef.current;
    const cursorDot = cursorDotRef.current;
    
    if (!cursor || !cursorDot) return;

    const onMouseMove = (e) => {
      gsap.to(cursor, {
        x: e.clientX - 16,
        y: e.clientY - 16,
        duration: 0.3,
        ease: 'power2.out',
      });
      
      gsap.to(cursorDot, {
        x: e.clientX - 4,
        y: e.clientY - 4,
        duration: 0.1,
        ease: 'power2.out',
      });
    };

    const onMouseDown = () => {
      gsap.to(cursor, { scale: 0.8, duration: 0.1 });
    };

    const onMouseUp = () => {
      gsap.to(cursor, { scale: 1, duration: 0.1 });
    };

    const onMouseEnterLink = () => {
      gsap.to(cursor, { scale: 1.5, duration: 0.2 });
    };

    const onMouseLeaveLink = () => {
      gsap.to(cursor, { scale: 1, duration: 0.2 });
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);

    // Add hover effect for interactive elements
    const interactiveElements = document.querySelectorAll('button, a, input, [role="button"]');
    interactiveElements.forEach((el) => {
      el.addEventListener('mouseenter', onMouseEnterLink);
      el.addEventListener('mouseleave', onMouseLeaveLink);
    });

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      interactiveElements.forEach((el) => {
        el.removeEventListener('mouseenter', onMouseEnterLink);
        el.removeEventListener('mouseleave', onMouseLeaveLink);
      });
    };
  }, []);

  return (
    <>
      {/* Heart cursor */}
      <div
        ref={cursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[9999] hidden lg:block"
        style={{ transform: 'translate(-50%, -50%)' }}
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
            fill="#F472B6"
            stroke="#BE185D"
            strokeWidth="1"
          />
          {/* Lens/magnifying effect circle */}
          <circle cx="12" cy="10" r="4" fill="none" stroke="white" strokeWidth="1.5" opacity="0.6" />
        </svg>
      </div>
      {/* Center dot */}
      <div
        ref={cursorDotRef}
        className="fixed top-0 left-0 w-2 h-2 bg-rose-500 rounded-full pointer-events-none z-[10000] hidden lg:block"
        style={{ transform: 'translate(-50%, -50%)' }}
      />
    </>
  );
};

export default HeartCursor;
