import React, { useState } from "react";
import IDBadge from "./components/IDBadge/IDBadge.jsx";

const SAMPLE_PRESETS = {
  instructor: {
    fullName: "SARA ALAOUI",
    role: "LANGUAGE INSTRUCTOR",
    id: "1234567890",
    phone: "+33 6 12 34 56 78",
    email: "info@ilas-ecole.com",
    qrCodeData: "ILAS|INSTRUCTOR|1234567890|SARA ALAOUI",
    barcodeData: "1234567890",
    photo: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80",
  },
  student: {
    fullName: "THOMAS DUBOIS",
    role: "STUDENT",
    id: "9876543210",
    phone: "+33 7 89 01 23 45",
    email: "t.dubois@ilas-ecole.com",
    qrCodeData: "ILAS|STUDENT|9876543210|THOMAS DUBOIS",
    barcodeData: "9876543210",
    photo: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=400&auto=format&fit=crop&q=80",
  },
};

export default function App() {
  const [mode, setMode] = useState("preview"); // "preview" | "edit"
  const [badgeData, setBadgeData] = useState(SAMPLE_PRESETS.instructor);

  const handleChange = (field) => (e) => {
    setBadgeData({ ...badgeData, [field]: e.target.value });
  };

  const applyPreset = (key) => {
    if (SAMPLE_PRESETS[key]) {
      setBadgeData(SAMPLE_PRESETS[key]);
    }
  };

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 28 }}>🪪</span>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, color: "#1B3D8F", fontWeight: 700 }}>
              ID Badge Generator
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: "#5b6472" }}>
              CR80 Standard Card (85.6mm × 54mm) • % Percentage Positioning • PNG & PDF Export
            </p>
          </div>
        </div>

        {/* Mode Toggle Buttons */}
        <div style={toggleContainerStyle}>
          <button
            onClick={() => setMode("preview")}
            style={{
              ...toggleBtnStyle,
              background: mode === "preview" ? "#1B3D8F" : "transparent",
              color: mode === "preview" ? "#ffffff" : "#1B3D8F",
            }}
          >
            👁️ Preview Mode
          </button>
          <button
            onClick={() => setMode("edit")}
            style={{
              ...toggleBtnStyle,
              background: mode === "edit" ? "#1B3D8F" : "transparent",
              color: mode === "edit" ? "#ffffff" : "#1B3D8F",
            }}
          >
            ✏️ Edit Mode
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <main style={mainLayoutStyle}>
        {/* Left Side: Live Badge Render */}
        <section style={cardSectionStyle}>
          <div style={{ width: "100%", maxWidth: 540 }}>
            <IDBadge {...badgeData} showActions={true} />
          </div>
        </section>

        {/* Right Side: Edit Form (Visible in Edit Mode or Side-by-side) */}
        {mode === "edit" && (
          <aside style={formPanelStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0, color: "#1B3D8F", fontSize: 16, fontWeight: 700 }}>
                Edit Badge Data
              </h3>
              <div style={{ display: "flex", gap: 6 }}>
                <button onClick={() => applyPreset("instructor")} style={presetBtnStyle}>
                  Instructor
                </button>
                <button onClick={() => applyPreset("student")} style={presetBtnStyle}>
                  Student
                </button>
              </div>
            </div>

            <div style={formGridStyle}>
              <FormField label="Full Name" value={badgeData.fullName} onChange={handleChange("fullName")} />
              <FormField label="Role / Badge Label" value={badgeData.role} onChange={handleChange("role")} />
              <FormField label="Main ID" value={badgeData.id} onChange={handleChange("id")} />
              <FormField label="Phone" value={badgeData.phone} onChange={handleChange("phone")} />
              <FormField label="Email" value={badgeData.email} onChange={handleChange("email")} />
              <FormField label="Photo URL" value={badgeData.photo} onChange={handleChange("photo")} placeholder="https://..." />
              <FormField label="QR Code Data" value={badgeData.qrCodeData} onChange={handleChange("qrCodeData")} />
              <FormField label="Barcode Data (CODE128)" value={badgeData.barcodeData} onChange={handleChange("barcodeData")} />
            </div>
          </aside>
        )}
      </main>
    </div>
  );
}

function FormField({ label, value, onChange, placeholder = "" }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 12, fontWeight: 600, color: "#1B3D8F" }}>{label}</span>
      <input
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        style={inputStyle}
      />
    </label>
  );
}

// Inline Demo Styles
const containerStyle = {
  maxWidth: 1100,
  margin: "0 auto",
  padding: "32px 24px",
  fontFamily: "'Roboto', sans-serif",
  color: "#1B3D8F",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  flexWrap: "wrap",
  gap: 16,
  marginBottom: 28,
  paddingBottom: 20,
  borderBottom: "1px solid #e2e8f0",
};

const toggleContainerStyle = {
  display: "flex",
  background: "#edf2f7",
  borderRadius: 10,
  padding: 4,
};

const toggleBtnStyle = {
  border: "none",
  padding: "8px 18px",
  borderRadius: 8,
  fontSize: 13,
  fontWeight: 600,
  cursor: "pointer",
  transition: "all 0.2s ease",
};

const mainLayoutStyle = {
  display: "flex",
  gap: 32,
  alignItems: "flex-start",
  flexWrap: "wrap",
};

const cardSectionStyle = {
  flex: "1 1 480px",
  display: "flex",
  justifyContent: "center",
};

const formPanelStyle = {
  flex: "1 1 360px",
  background: "#ffffff",
  padding: 24,
  borderRadius: 16,
  border: "1px solid #e2e8f0",
  boxShadow: "0 10px 25px rgba(27, 61, 143, 0.08)",
};

const formGridStyle = {
  display: "grid",
  gridTemplateColumns: "1fr",
  gap: 12,
};

const inputStyle = {
  padding: "9px 12px",
  borderRadius: 8,
  border: "1.5px solid #cbd5e1",
  fontSize: 13,
  outline: "none",
  transition: "border 0.2s ease",
};

const presetBtnStyle = {
  padding: "4px 10px",
  borderRadius: 6,
  border: "1px solid #cbd5e1",
  background: "#f8fafc",
  color: "#1B3D8F",
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
};
