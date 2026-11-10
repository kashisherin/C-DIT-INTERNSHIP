
import { useEffect, useState } from "react";
import { getDepartments } from "../api";
import GrievanceUpload from "../components/GrievanceUpload";
import { useLanguage } from "../context/LanguageContext";

const FIELD =
    "mt-1 w-full rounded-xl border border-gray-300 p-3 text-gray-800 " +
    "focus:border-blue-500 focus:outline-none";

const DEPARTMENT_NAMES_ML = {
    KWA: "കേരള ജല അതോറിറ്റി",
    KSEB: "കേരള സംസ്ഥാന വൈദ്യുതി ബോർഡ്",
    PWD: "പൊതുമരാമത്ത് വകുപ്പ്",
    LSGD: "തദ്ദേശ സ്വയംഭരണ വകുപ്പ്",
    REVENUE: "റവന്യൂ വകുപ്പ്",
    POLICE: "പോലീസ് വകുപ്പ്",
    HEALTH: "ആരോഗ്യ വകുപ്പ്",
    EDUCATION: "വിദ്യാഭ്യാസ വകുപ്പ്",
    CIVIL_SUPPLIES: "സിവിൽ സപ്ലൈസ് വകുപ്പ്",
    SOCIAL_JUSTICE: "സാമൂഹ്യനീതി വകുപ്പ്",
    TRANSPORT: "ഗതാഗത വകുപ്പ്",
    OTHER: "മറ്റുള്ളവ",
};

export default function OfficialPage() {
    const [departments, setDepartments] = useState([]);
    const [summary, setSummary] = useState("");
    const [description, setDescription] = useState("");
    const [department, setDepartment] = useState("");
    const [aiNote, setAiNote] = useState("");

    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    // Load the department list once
    useEffect(() => {
        getDepartments()
            .then(setDepartments)
            .catch((error) => setAiNote(error.message));
    }, []);

    // Fill the form with the AI's answer
    function handleResult(result) {
        setSummary(result.summary);
        setDescription(result.description);
        setDepartment(result.department);

        setAiNote(
            isMalayalam
                ? `AI നിർദ്ദേശിക്കുന്ന വകുപ്പ്: ${
                    DEPARTMENT_NAMES_ML[result.department] ||
                    result.department_name
                } — ${result.department_reason}`
                : `AI suggests ${result.department_name}: ${result.department_reason}`
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
                        {isMalayalam ? "ഔദ്യോഗിക പോർട്ടൽ" : "Official view"}
                    </h1>

                    <p className="mt-2 text-gray-600">
                        {isMalayalam
                            ? "പരാതി അപ്‌ലോഡ് ചെയ്യുക. AI വിവരങ്ങൾ പൂരിപ്പിക്കും. തുടർന്ന് പരിശോധിച്ച് അനുയോജ്യമായ വകുപ്പിലേക്ക് അയയ്ക്കുക."
                            : "Upload a grievance, let the AI pre-fill the details, then review and route it."}
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
                            {isMalayalam
                                ? "പരാതിയുടെ വിശദാംശങ്ങൾ"
                                : "Grievance details"}
                        </h2>

                        {summary && (
                            <div className="mb-5 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
                                {isMalayalam
                                    ? "AI വിവരങ്ങൾ പൂരിപ്പിച്ചിട്ടുണ്ട്. വകുപ്പിലേക്ക് അയയ്ക്കുന്നതിന് മുമ്പ് എല്ലാ വിവരങ്ങളും പരിശോധിക്കുക."
                                    : "Pre-filled by AI. Review every field before routing."}
                            </div>
                        )}

                        <div className="space-y-5">

                            {/* Summary */}
                            <div>
                                <label
                                    htmlFor="summary"
                                    className="text-sm font-semibold text-gray-700"
                                >
                                    {isMalayalam
                                        ? "പരാതിയുടെ സംഗ്രഹം"
                                        : "Summary"}
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
                                    {isMalayalam
                                        ? "പൂർണ്ണമായ വിവരണം"
                                        : "Full description"}
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
                                    {isMalayalam
                                        ? "പരാതി അയയ്ക്കേണ്ട വകുപ്പ്"
                                        : "Department to route to"}
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
                                        {isMalayalam
                                            ? "ഒരു വകുപ്പ് തിരഞ്ഞെടുക്കുക"
                                            : "Select a department"}
                                    </option>

                                    {departments.map((d) => (
                                        <option
                                            key={d.code}
                                            value={d.code}
                                        >
                                            {d.code} - {
                                                isMalayalam
                                                    ? DEPARTMENT_NAMES_ML[d.code] || d.name
                                                    : d.name
                                            }
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
