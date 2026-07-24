import { useState } from "react";

import "../styles/Upload.css";
import axios from "axios";

export default function Upload({ onSuccess, setLoading }) {
    const [file, setFile] = useState(null);
    const [message, setMessage] = useState("");
    const [isUploading, setIsUploading] = useState(false);

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        setMessage("");
    };

    const handleUpload = async () => {
        if (!file) {
            alert("Please select a PDF file.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            setLoading(true);
            setIsUploading(true);
            setMessage("");

            // Upload PDF
            const uploadResponse = await axios.post(
                "http://127.0.0.1:8000/api/upload",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );

            console.log("Upload Response:", uploadResponse.data);

            // Support different backend response keys
            const filename =
                uploadResponse.data.filename ||
                uploadResponse.data.file_name ||
                uploadResponse.data.saved_filename ||
                uploadResponse.data.name;

            if (!filename) {
                throw new Error(
                    "Backend did not return a filename.\nResponse: " +
                    JSON.stringify(uploadResponse.data)
                );
            }

            console.log("Filename:", filename);

            // Extract data
            const extractResponse = await axios.get(
                `http://127.0.0.1:8000/api/bl-extract/${filename}`
            );

            console.log("Extract Response:", extractResponse.data);

            onSuccess(extractResponse.data);

            setMessage("✅ Extraction completed successfully.");
        } catch (error) {
            console.error(error);

            if (error.response) {
                console.log("Backend Error:", error.response.data);
            }

            setMessage("❌ Failed to extract Bill of Lading.");
        } finally {
            setLoading(false);
            setIsUploading(false);
        }
    };

    return (
        <div className="upload-card">

            <div className="upload-icon">📄</div>

            <h2>Upload Bill of Lading</h2>

            <p className="upload-subtitle">
                Select a Bill of Lading PDF to extract shipment information using
                OCR and Gemini AI.
            </p>

            <label className="file-input-label">
                📁 Choose PDF File
                <input
                    type="file"
                    accept=".pdf"
                    onChange={handleFileChange}
                    hidden
                />
            </label>

            {file && (
                <p className="selected-file">
                    ✅ {file.name}
                </p>
            )}

            <button
                className="extract-btn"
                onClick={handleUpload}
                disabled={isUploading}
            >
                {isUploading ? "⏳ Processing..." : "🚀 Extract Information"}
            </button>

            {message && (
                <p className="upload-message">
                    {message}
                </p>
            )}

        </div>
    );
}