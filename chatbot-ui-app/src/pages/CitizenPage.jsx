import { useState } from "react";
import GrievanceUpload from "../components/GrievanceUpload";
import { useLanguage } from "../context/LanguageContext";

const FIELD =
    "mt-1 w-full rounded-xl border border-gray-300 bg-gray-50 p-3 text-gray-800 " +
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

export default function CitizenPage() {
    const [summary, setSummary] = useState("");
    const [description, setDescription] = useState("");
    const [department, setDepartment] = useState("");
    const [departmentReason, setDepartmentReason] = useState("");
    const [registration, setRegistration] = useState(null);

    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    // Display the analysis and registration details returned by the backend.
    // The backend has already registered the grievance at this point.
    function handleResult(result) {
        const departmentCode = result?.department || "";
        const departmentName = result?.department_name || departmentCode;
        const reason = result?.department_reason || "";

        setSummary(result?.summary || "");
        setDescription(result?.description || "");
        setDepartment(departmentCode);

        setRegistration({
            grievanceId: result?.grievance_id || "",
            departmentSlot: result?.department_slot ?? "",
            departmentCode,
            departmentName,
            status: result?.status || "REGISTERED",
            citizenName: result?.citizen_name || "",
        });

        setDepartmentReason(reason);
    }

    function handleClear() {
        setSummary("");
        setDescription("");
        setDepartment("");
        setDepartmentReason("");
        setRegistration(null);
    }

    const displayedDepartmentName = department
        ? isMalayalam
            ? DEPARTMENT_NAMES_ML[department] || registration?.departmentName || department
            : registration?.departmentName || department
        : isMalayalam
            ? "ലഭ്യമല്ല"
            : "Not available";

    return (
        <main className="min-h-screen bg-gray-50 px-6 py-10">
            <div className="mx-auto max-w-5xl">
                {/* Citizen portal heading */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">
                        {isMalayalam ? "പൗര പോർട്ടൽ" : "Citizen Portal"}
                    </h1>

                    <p className="mt-2 text-gray-600">
                        {isMalayalam
                            ? "പരാതി അപ്‌ലോഡ് ചെയ്യുക. AI അത് വിശകലനം ചെയ്ത് അനുയോജ്യമായ വകുപ്പിൽ രജിസ്റ്റർ ചെയ്യും. രജിസ്ട്രേഷൻ വിവരങ്ങൾ സൂക്ഷിക്കുക."
                            : "Upload your grievance. AI analyses it and registers it under the appropriate department. Keep your registration details for future reference."}
                    </p>
                </div>

                {/* Successful grievance registration confirmation */}
                {registration && (
                    <div className="mb-8 rounded-2xl border border-green-200 bg-green-50 p-5 shadow-sm">
                        <h2 className="text-lg font-bold text-green-800">
                            {isMalayalam
                                ? "പരാതി വിജയകരമായി രജിസ്റ്റർ ചെയ്തു"
                                : "Grievance Successfully Registered"}
                        </h2>

                        <p className="mt-1 text-sm text-green-700">
                            {isMalayalam
                                ? "നിങ്ങളുടെ പരാതിയുടെ രജിസ്ട്രേഷൻ വിവരങ്ങൾ താഴെ നൽകുന്നു."
                                : "Your grievance has been saved successfully. Keep your registration details for future reference."}
                        </p>

                        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            <div className="rounded-lg bg-white p-3">
                                <p className="text-xs text-gray-500">
                                    {isMalayalam ? "പൗരന്റെ പേര്" : "Citizen Name"}
                                </p>
                                <p className="mt-1 break-words font-semibold text-gray-800">
                                    {registration.citizenName ||
                                        (isMalayalam
                                            ? "പേര് തിരിച്ചറിയാനായില്ല"
                                            : "Name not identified")}
                                </p>
                            </div>

                            <div className="rounded-lg bg-white p-3">
                                <p className="text-xs text-gray-500">
                                    {isMalayalam ? "രജിസ്ട്രേഷൻ ID" : "Grievance ID"}
                                </p>
                                <p className="mt-1 break-all font-bold text-blue-700">
                                    {registration.grievanceId || "—"}
                                </p>
                            </div>

                            <div className="rounded-lg bg-white p-3">
                                <p className="text-xs text-gray-500">
                                    {isMalayalam ? "വകുപ്പ് സ്ലോട്ട്" : "Department Slot"}
                                </p>
                                <p className="mt-1 text-xl font-bold text-gray-800">
                                    {registration.departmentSlot || "—"}
                                </p>
                            </div>

                            <div className="rounded-lg bg-white p-3">
                                <p className="text-xs text-gray-500">
                                    {isMalayalam ? "ബന്ധപ്പെട്ട വകുപ്പ്" : "Department"}
                                </p>
                                <p className="mt-1 font-semibold text-gray-800">
                                    {registration.departmentCode || "—"}
                                </p>
                                <p className="text-sm text-gray-600">
                                    {isMalayalam
                                        ? DEPARTMENT_NAMES_ML[registration.departmentCode] || registration.departmentName
                                        : registration.departmentName}
                                </p>
                            </div>

                            <div className="rounded-lg bg-white p-3">
                                <p className="text-xs text-gray-500">
                                    {isMalayalam ? "നില" : "Registration Status"}
                                </p>
                                <p className="mt-1 font-semibold text-green-700">
                                    {registration.status}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Grievance upload and AI-generated details */}
                <div className="grid gap-8 lg:grid-cols-2">
                    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                        <GrievanceUpload
                            onResult={handleResult}
                            onClear={handleClear}
                        />
                    </div>

                    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                        <h2 className="mb-5 text-xl font-semibold text-gray-800">
                            {isMalayalam
                                ? "പരാതിയുടെ വിശദാംശങ്ങൾ"
                                : "Grievance details"}
                        </h2>

                        {summary && (
                            <div className="mb-5 rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
                                {isMalayalam
                                    ? "AI തയ്യാറാക്കിയ സംഗ്രഹവും വിവരണവും. നിങ്ങളുടെ പരാതി ഇതിനകം രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്."
                                    : "AI-generated summary and description. Your grievance has already been registered."}
                            </div>
                        )}

                        <div className="space-y-5">
                            {/* AI-generated summary: read-only for citizens */}
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
                                    readOnly
                                    placeholder={
                                        isMalayalam
                                            ? "AI തയ്യാറാക്കുന്ന സംഗ്രഹം ഇവിടെ കാണിക്കും."
                                            : "The AI-generated summary will appear here."
                                    }
                                    className={`${FIELD} read-only:cursor-default`}
                                />
                            </div>

                            {/* AI-generated description: read-only for citizens */}
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
                                    readOnly
                                    placeholder={
                                        isMalayalam
                                            ? "AI തയ്യാറാക്കുന്ന പൂർണ്ണ വിവരണം ഇവിടെ കാണിക്കും."
                                            : "The AI-generated description will appear here."
                                    }
                                    className={`${FIELD} read-only:cursor-default`}
                                />
                            </div>

                            {/* Department is assigned by AI, not selected by the citizen */}
                            <div>
                                <label
                                    htmlFor="ai-department"
                                    className="text-sm font-semibold text-gray-700"
                                >
                                    {isMalayalam
                                        ? "AI നിർദ്ദേശിച്ച വകുപ്പ്"
                                        : "AI-classified department"}
                                </label>

                                <div
                                    id="ai-department"
                                    className={`${FIELD} min-h-12`}
                                >
                                    <p className="font-semibold">
                                        {department || (isMalayalam ? "ലഭ്യമല്ല" : "Not available")}
                                    </p>
                                    {department && (
                                        <p className="mt-1 text-sm text-gray-600">
                                            {displayedDepartmentName}
                                        </p>
                                    )}
                                </div>

                                {department && (
                                    <p className="mt-2 text-xs leading-relaxed text-gray-500">
                                        {isMalayalam
                                            ? `AI നിർദ്ദേശിച്ച വകുപ്പ്: ${displayedDepartmentName}${departmentReason ? ` — ${departmentReason}` : ""}`
                                            : `AI classified this grievance under ${displayedDepartmentName}.${departmentReason ? ` ${departmentReason}` : ""}`}
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
