import "../styles/Loading.css";

export default function Loading() {

    return (

        <div className="loading-overlay">

            <div className="loading-card">

                <div className="loader"></div>

                <h2>🤖 AI Processing Bill of Lading</h2>

                <p className="loading-text">
                    Please wait while the document is being analyzed.
                </p>

                <div className="loading-steps">

                    <div>📄 Reading PDF...</div>

                    <div>🔍 Running OCR...</div>

                    <div>🤖 Extracting information using Gemini AI...</div>

                    <div>📊 Generating Excel Report...</div>

                </div>

            </div>

        </div>

    );

}