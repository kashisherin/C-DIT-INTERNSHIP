import { useEffect, useState } from "react";
import { getDepartments } from "../api";
import GrievanceUpload from "../components/GrievanceUpload";

const FIELD =
    "mt-1 w-full rounded-xl border border-gray-300 p-3 text-gray-800 " +
    "focus:border-blue-500 focus:outline-none";

export default function OfficialPage() {
    const [departments, setDepartments] = useState([]);
    const [summary, setSummary] = useState("");
    const [description, setDescription] = useState("");
    const [department, setDepartment] = useState("");
    const [aiNote, setAiNote] = useState("");

    // Load the department list once, for the dropdown
    useEffect(() => {
        getDepartments()
            .then(setDepartments)
            .catch((error) => setAiNote(error.message));
    }, []);

    // Fill the form with the AI's answer.
    // The official can still change everything.
    function handleResult(result) {
        setSummary(result.summary);
        setDescription(result.description);
        setDepartment(result.department);

        setAiNote(
            `AI suggests ${result.department_name}: ${result.department_reason}`
        );
    }

    function handleClear() {
        setSummary("");
        setDescription("");
        setDepartment("");
        setAiNote("");
    }

    return (
        <main className="min-h-screen bg-gray-50 px-6 py-10">
            <div className="mx-auto max-w-5xl">
                {/* Page heading */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">
                        Official view
                    </h1>

                    <p className="mt-2 text-gray-600">
                        Upload a grievance, let the AI pre-fill the details,
                        then review and route it.
                    </p>
                </div>

                {/* Grievance upload section */}
                <div className="grid gap-8 lg:grid-cols-2">
                    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                        <GrievanceUpload
                            onResult={handleResult}
                            onClear={handleClear}
                        />
                    </div>

                    {/* AI-generated grievance details */}
                    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                        <h2 className="mb-5 text-xl font-semibold text-gray-800">
                            Grievance details
                        </h2>

                        {summary && (
                            <div className="mb-5 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
                                Pre-filled by AI. Review every field before
                                routing.
                            </div>
                        )}

                        <div className="space-y-5">
                            {/* Summary */}
                            <div>
                                <label
                                    htmlFor="summary"
                                    className="text-sm font-semibold text-gray-700"
                                >
                                    Summary
                                </label>

                                <textarea
                                    id="summary"
                                    rows={3}
                                    value={summary}
                                    className={FIELD}
                                    onChange={(event) =>
                                        setSummary(event.target.value)
                                    }
                                />
                            </div>

                            {/* Full description */}
                            <div>
                                <label
                                    htmlFor="description"
                                    className="text-sm font-semibold text-gray-700"
                                >
                                    Full description
                                </label>

                                <textarea
                                    id="description"
                                    rows={9}
                                    value={description}
                                    className={FIELD}
                                    onChange={(event) =>
                                        setDescription(event.target.value)
                                    }
                                />
                            </div>

                            {/* Department selection */}
                            <div>
                                <label
                                    htmlFor="department"
                                    className="text-sm font-semibold text-gray-700"
                                >
                                    Department to route to
                                </label>

                                <select
                                    id="department"
                                    value={department}
                                    className={FIELD}
                                    onChange={(event) =>
                                        setDepartment(event.target.value)
                                    }
                                >
                                    <option value="">
                                        Select a department
                                    </option>

                                    {departments.map((d) => (
                                        <option
                                            key={d.code}
                                            value={d.code}
                                        >
                                            {d.code} - {d.name}
                                        </option>
                                    ))}
                                </select>

                                {aiNote && (
                                    <p className="mt-1 text-xs text-gray-500">
                                        {aiNote}
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}