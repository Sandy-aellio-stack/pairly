import React, { useEffect } from "react";

export default function LandingWrapper() {

  useEffect(() => {
    // Ensure page has no body scroll issues
    document.body.style.margin = "0";
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  return (
    <iframe
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
