import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

export default function LandingWrapper() {
  const navigate = useNavigate();
  const iframeRef = useRef(null);

  useEffect(() => {
    // Listen for postMessage from the iframe
    const handleMessage = (event) => {
      // Verify the origin if needed
      if (event.data && event.data.type === "navigate") {
        navigate(event.data.path);
      }
    };

    window.addEventListener("message", handleMessage);
    
    // Ensure page has no body scroll issues
    document.body.style.margin = "0";
    document.body.style.overflow = "hidden";
    
    return () => {
      window.removeEventListener("message", handleMessage);
      document.body.style.overflow = "auto";
    };
  }, [navigate]);

  return (
    <iframe
      ref={iframeRef}
      src="/landing/index.html"
      title="Landing"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        border: "none",
        overflow: "hidden"
      }}
    />
  );
}
