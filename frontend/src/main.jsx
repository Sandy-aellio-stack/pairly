import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import HeartCursor from "@/components/HeartCursor";

const Root = () => (
  <>
    <HeartCursor />
    <App />
  </>
);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);

