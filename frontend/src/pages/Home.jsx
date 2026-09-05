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

    const data = result?.data;

    const header = data?.header || null;

    const containers =
        data?.containers?.containers || [];

    const summary = data?.summary || null;

    const excelFile = result?.excel_file || null;

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
                            header={header}
                        />

                        <ContainerTable
                            containers={containers}
                        />

                        <SummaryCard
                            summary={summary}
                        />

                        <DownloadButtons
                            excelFile={excelFile}
                            data={data}
                        />
                    </>

                )}

                <Footer />

            </div>
        </>

    );
}