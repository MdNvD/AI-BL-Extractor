import "../styles/DownloadButtons.css";

export default function DownloadButtons({ excelFile, data }) {

    if (!excelFile) return null;

    const downloadJson = () => {

        const blob = new Blob(
            [JSON.stringify(data, null, 4)],
            { type: "application/json" }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = url;
        link.download = "bill_of_lading.json";

        link.click();

        URL.revokeObjectURL(url);

    };

    const downloadExcel = () => {

        window.open(
            `http://127.0.0.1:8000/api/download-excel/${excelFile}`,
            "_blank"
        );

    };

    return (

        <div className="download-section">

            <h2>📥 Export Results</h2>

            <p>
                Download the extracted Bill of Lading information in your preferred format.
            </p>

            <div className="download-actions">

                <button
                    className="excel-btn"
                    onClick={downloadExcel}
                >
                    📊 Download Excel
                </button>

                <button
                    className="json-btn"
                    onClick={downloadJson}
                >
                    📄 Download JSON
                </button>

            </div>

        </div>

    );

}