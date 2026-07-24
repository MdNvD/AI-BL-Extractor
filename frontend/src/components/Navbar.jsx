import "../styles/Navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div>
          <h1>🤖 AI Bill of Lading Extractor</h1>
          <p>Fast • Accurate • OCR + Gemini AI Powered</p>
        </div>

        <div className="badge">
          AI Document Intelligence
        </div>
      </div>
    </nav>
  );
}

export default Navbar;