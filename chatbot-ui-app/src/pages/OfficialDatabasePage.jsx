import { Link } from "react-router";
import { useLanguage } from "../context/LanguageContext";
import DatabaseManagementPage from "./DatabaseManagementPage";

export default function OfficialDatabasePage({ username }) {
    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    return (
        <main className="min-h-[calc(100vh-73px)] bg-slate-50">
            <header className="flex flex-col gap-3 border-b border-gray-200 bg-white px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-8">
                <div>
                    <h1 className="text-xl font-bold text-gray-800">
                        {isMalayalam ? "ഡാറ്റാബേസ് മാനേജ്മെന്റ്" : "Database Management"}
                    </h1>
                    <p className="mt-1 text-xs text-gray-500">
                        {isMalayalam
                            ? "രജിസ്റ്റർ ചെയ്ത പരാതികളും അവയുടെ രേഖകളും നിയന്ത്രിക്കുക."
                            : "Manage registered grievances and their uploaded documents."}
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                    <span className="hidden text-sm text-gray-500 sm:inline">
                        {username}
                    </span>
                    <Link
                        to="/official"
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                        {isMalayalam ? "AI സഹായിയിലേക്ക് മടങ്ങുക" : "Back to AI Assistant"}
                    </Link>
                </div>
            </header>

            <DatabaseManagementPage />
        </main>
    );
}
