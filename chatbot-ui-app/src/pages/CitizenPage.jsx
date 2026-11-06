import { useState } from "react";
import GrievanceUpload from "../components/GrievanceUpload";

export default function CitizenPage() {
    const [summary, setSummary] = useState("");

    return (
        <main className="min-h-screen bg-gray-50 px-6 py-10">
            <div className="mx-auto max-w-3xl">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">
                        Submit a grievance
                    </h1>

                    <p className="mt-2 text-gray-600">
                        Upload a photo or scan of your letter. The AI assistant
                        reads it and writes a short summary.
                    </p>
                </div>

                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                    <GrievanceUpload
                        onResult={(result) => setSummary(result.summary)}
                        onClear={() => setSummary("")}
                    />

                    <div className="mt-8 border-t border-gray-200 pt-6">
                        <h2 className="text-lg font-semibold text-gray-800">
                            Summary of your grievance
                        </h2>

                        {summary && (
                            <>
                                <p className="mt-3 whitespace-pre-wrap text-gray-700">
                                    {summary}
                                </p>

                                <p className="mt-2 text-xs text-gray-500">
                                    Written by AI. Please check that it matches
                                    your letter.
                                </p>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}