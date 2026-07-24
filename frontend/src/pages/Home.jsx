import { useState } from "react";

import "../styles/Home.css";
import Navbar from "../components/Navbar";
import Upload from "../components/Upload";
import HeaderCard from "../components/HeaderCard";
import ContainerTable from "../components/ContainerTable";
import SummaryCard from "../components/SummaryCard";
import DownloadButtons from "../components/DownloadButtons";
import Loading from "../components/Loading";
import Footer from "../components/Footer";

export default function Home() {

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    return (

        <>
            <Navbar />

            <div className="home">

                <Upload
                    onSuccess={setResult}
                    setLoading={setLoading}
                />

                {loading && <Loading />}

                {result && (

                    <>
                        <HeaderCard
                            header={result.data.header}
                        />

                        <ContainerTable
                            containers={result.data.containers.containers}
                        />

                        <SummaryCard
                            summary={result.data.summary}
                        />

                        <DownloadButtons
                            excelFile={result.excel_file}
                            data={result.data}
                        />
                    </>

                )}

                <Footer />

            </div>
        </>

    );

}