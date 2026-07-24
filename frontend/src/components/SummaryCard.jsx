import "../styles/SummaryCard.css";

export default function SummaryCard({ summary }) {

    if (!summary) return null;

    const cards = [
        {
            icon: "📦",
            title: "Total Containers",
            value: summary.total_containers,
            color: "#2563eb"
        },
        {
            icon: "📦",
            title: "Total Cartons",
            value: summary.total_cartons,
            color: "#16a34a"
        },
        {
            icon: "⚖️",
            title: "Total Weight",
            value: `${summary.total_weight} KG`,
            color: "#ea580c"
        },
        {
            icon: "📐",
            title: "Total CBM",
            value: `${summary.total_cbm} CBM`,
            color: "#7c3aed"
        }
    ];

    return (

        <div className="summary-section">

            <h2>📊 Shipment Summary</h2>

            <div className="summary-grid">

                {cards.map((item) => (

                    <div
                        className="summary-box"
                        key={item.title}
                    >

                        <div
                            className="summary-icon"
                            style={{ background: item.color }}
                        >
                            {item.icon}
                        </div>

                        <h3>{item.title}</h3>

                        <p>{item.value}</p>

                    </div>

                ))}

            </div>

        </div>

    );

}