import "../styles/ContainerTable.css";

export default function ContainerTable({ containers }) {

    if (!containers || containers.length === 0) return null;

    return (

        <div className="container-card">

            <div className="table-header">

                <h2>📦 Container Details</h2>

                <span className="container-count">
                    {containers.length} Containers
                </span>

            </div>

            <div className="table-wrapper">

                <table className="container-table">

                    <thead>

                        <tr>
                            <th>#</th>
                            <th>Container No</th>
                            <th>Seal No</th>
                            <th>Size</th>
                            <th>Cartons</th>
                            <th>Weight (KG)</th>
                            <th>CBM</th>
                        </tr>

                    </thead>

                    <tbody>

                        {containers.map((container, index) => (

                            <tr key={index}>

                                <td>{index + 1}</td>

                                <td>
                                    {container.container_number || "-"}
                                </td>

                                <td>
                                    {container.seal_number || "-"}
                                </td>

                                <td>
                                    {container.size || "-"}
                                </td>

                                <td>
                                    {container.cartons ?? "-"}
                                </td>

                                <td>
                                    {container.weight_kg ?? "-"}
                                </td>

                                <td>
                                    {container.cbm ?? "-"}
                                </td>

                            </tr>

                        ))}

                    </tbody>

                </table>

            </div>

        </div>

    );

}