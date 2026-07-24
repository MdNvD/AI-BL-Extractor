import "../styles/Footer.css";

export default function Footer() {

    return (

        <footer className="footer">

            <h3>🤖 AI Bill of Lading Extractor</h3>

            <p>
                Intelligent document extraction using OCR and Google Gemini AI.
            </p>

            <div className="footer-tech">

                <span>⚛ React</span>

                <span>⚡ FastAPI</span>

                <span>🤖 Gemini AI</span>

                <span>📄 OCR</span>

                <span>📊 Excel Export</span>

            </div>

            <div className="footer-bottom">

                Version 1.0 • © 2026 Mohamed Navith

            </div>

        </footer>

    );

}