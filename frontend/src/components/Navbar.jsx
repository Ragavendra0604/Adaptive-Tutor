import React from "react";
import { Link, useLocation } from "react-router-dom";

const navStyle = {
  background: "#020617",
  borderBottom: "1px solid #1f2937",
  padding: "0.75rem 1.5rem"
};

const innerStyle = {
  maxWidth: "1100px",
  margin: "0 auto",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between"
};

const linkRow = {
  display: "flex",
  gap: "1rem",
  fontSize: "0.95rem"
};

function NavLink({ to, label }) {
  const location = useLocation();
  const active = location.pathname === to;
  return (
    <Link
      to={to}
      style={{
        textDecoration: "none",
        color: active ? "#38bdf8" : "#9ca3af",
        fontWeight: active ? 600 : 400
      }}
    >
      {label}
    </Link>
  );
}

export default function Navbar() {
  return (
    <header style={navStyle}>
      <div style={innerStyle}>
        <div style={{ fontWeight: 700, color: "#f9fafb" }}>Adaptive DSA Tutor</div>
        <nav style={linkRow}>
          <NavLink to="/" label="Chat" />
          <NavLink to="/practice" label="Practice" />
          <NavLink to="/admin" label="Admin" />
        </nav>
      </div>
    </header>
  );
}
