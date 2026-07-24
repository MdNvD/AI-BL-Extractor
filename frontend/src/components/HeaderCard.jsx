import "../styles/HeaderCard.css";

export default function HeaderCard({ header }) {

    if (!header) return null;

    const fields = [
        ["Carrier", header.carrier],
        ["Bill of Lading No", header.bill_of_lading_number],
        ["Vessel", header.vessel],
        ["Voyage", header.voyage],
        ["Port of Loading", header.port_of_loading],
        ["Port of Discharge", header.port_of_discharge],
        ["Place of Receipt", header.place_of_receipt],
        ["Place of Delivery", header.place_of_delivery],
        ["Freight", header.freight],
        ["Shipper", header.shipper],
        ["Consignee", header.consignee],
        ["Notify Party", header.notify_party],
    ];

    return (

        <div className="header-card">

            <h2>📋 Shipment Information</h2>

            <div className="header-grid">

                {fields.map(([label, value]) => (

                    <div className="header-item" key={label}>

                        <span className="label">{label}</span>

                        <span className="value">
                            {value || "-"}
                        </span>

                    </div>

                ))}

            </div>

        </div>

    );

}