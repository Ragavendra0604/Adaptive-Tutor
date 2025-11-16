import React from "react";
import Navbar from "./Navbar";

const layoutStyle = {
  minHeight: "100vh",
  background: "#0f172a",
  color: "#e5e7eb"
};

const contentStyle = {
  maxWidth: "1100px",
  margin: "0 auto",
  padding: "1.5rem"
};

export default function Layout({ children }) {
  return (
    <div style={layoutStyle}>
      <Navbar />
      <main style={contentStyle}>{children}</main>
    </div>
  );
}
