
import { NavLink } from "react-router";
import { useLanguage } from "../context/LanguageContext";

// NavLink knows whether its page is open, so we can highlight it
function linkStyle({ isActive }) {
    return isActive
        ? "rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white"
        : "rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100";
}

export default function NavBar() {
    const { language, setLanguage } = useLanguage();

    return (
        <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
            {/* Website title */}
            <div>
                <h1 className="text-xl font-bold text-gray-800">
                    {language === "en" ? "Grievance Portal" : "പരാതി പോർട്ടൽ"}
                </h1>

                <p className="text-sm text-gray-500">
                    {language === "en"
                        ? "AI-assisted grievance processing"
                        : "AI സഹായത്തോടെയുള്ള പരാതി പരിഹാരം"}
                </p>
            </div>

            {/* Navigation links and language switch */}
            <div className="flex items-center gap-3">
                <NavLink to="/" className={linkStyle}>
                    {language === "en" ? "Citizen" : "പൗരൻ"}
                </NavLink>

                <NavLink to="/official" className={linkStyle}>
                    {language === "en" ? "Official" : "ഉദ്യോഗസ്ഥൻ"}
                </NavLink>

                <button
                    onClick={() =>
                        setLanguage(language === "en" ? "ml" : "en")
                    }
                    className="rounded-lg border border-blue-600 px-3 py-2 text-sm font-semibold text-blue-600 transition hover:bg-blue-50"
                >
                    {language === "en" ? "മലയാളം" : "English"}
                </button>
            </div>
        </nav>
    );
}
