
import {
    createContext,
    useContext,
    useEffect,
    useState,
} from "react";

const LanguageContext = createContext(null);

const translations = {
    en: {
        appTitle: "Grievance Portal",
        appSubtitle: "AI-assisted grievance processing",
        citizen: "Citizen",
        official: "Official",

        citizenTitle: "Submit a grievance",
        citizenDescription:
            "Upload a photo or scan of your letter. The AI assistant reads it and writes a short summary.",
        grievanceSummary: "Summary of your grievance",
        aiWritten: "Written by AI. Please check that it matches your letter.",

        officialTitle: "Official view",
        officialDescription:
            "Upload a grievance, let the AI pre-fill the details, then review and route it.",
        grievanceDetails: "Grievance details",
        aiPrefilled: "Pre-filled by AI. Review every field before routing.",
        summary: "Summary",
        fullDescription: "Full description",
        department: "Department to route to",
        selectDepartment: "Select a department",

        grievanceLetter: "Grievance letter",
        photoOrScan: "Photo or scan, handwritten or typed",
        chooseFile: "Click to choose a file, or drop it here",
        supportedFiles: "JPG, PNG, WEBP or PDF, up to 10 MB",
        processWithAI: "Process with AI",
        readingLetter: "Reading the letter...",
        processingInfo:
            "The AI is reading the document. This can take 1-3 minutes on a laptop.",

        chatbotTitle: "Kerala Assistant",
        chatbotWelcome:
            "Hi! Ask me anything about Kerala and its government services.",
        chatbotSubtitle: "Answers from official web pages",
        chatPlaceholder: "Ask a question about Kerala...",
        send: "Send",
        sources: "Sources",
        closeChat: "Close chat",
        openChat: "Open chat",

        language: "Language",
        english: "English",
        malayalam: "മലയാളം",

        selectFileError: "Please select a file.",
        unsupportedFile: "Unsupported file format.",
        uploadError: "Unable to process the uploaded file.",
        apiError: "Cannot reach the API. Is the backend running?",
    },

    ml: {
        appTitle: "പരാതി പരിഹാര പോർട്ടൽ",
        appSubtitle: "AI സഹായത്തോടെയുള്ള പരാതി സംസ്കരണം",
        citizen: "പൗരൻ",
        official: "ഉദ്യോഗസ്ഥൻ",

        citizenTitle: "പരാതി സമർപ്പിക്കുക",
        citizenDescription:
            "നിങ്ങളുടെ പരാതിക്കത്തിന്റെ ഫോട്ടോയോ സ്കാനോ അപ്‌ലോഡ് ചെയ്യുക. AI അത് വായിച്ച് ഒരു സംഗ്രഹം തയ്യാറാക്കും.",
        grievanceSummary: "നിങ്ങളുടെ പരാതിയുടെ സംഗ്രഹം",
        aiWritten:
            "AI തയ്യാറാക്കിയതാണ്. നിങ്ങളുടെ പരാതിയുമായി ഇത് പൊരുത്തപ്പെടുന്നുണ്ടെന്ന് പരിശോധിക്കുക.",

        officialTitle: "ഉദ്യോഗസ്ഥരുടെ വിഭാഗം",
        officialDescription:
            "പരാതി അപ്‌ലോഡ് ചെയ്യുക. AI വിവരങ്ങൾ പൂരിപ്പിക്കും. തുടർന്ന് പരിശോധിച്ച് ബന്ധപ്പെട്ട വകുപ്പിലേക്ക് അയയ്ക്കുക.",
        grievanceDetails: "പരാതിയുടെ വിവരങ്ങൾ",
        aiPrefilled:
            "AI പൂരിപ്പിച്ച വിവരങ്ങളാണിവ. അയയ്ക്കുന്നതിന് മുമ്പ് എല്ലാ വിവരങ്ങളും പരിശോധിക്കുക.",
        summary: "സംഗ്രഹം",
        fullDescription: "പൂർണ്ണ വിവരണം",
        department: "ബന്ധപ്പെട്ട വകുപ്പ്",
        selectDepartment: "ഒരു വകുപ്പ് തിരഞ്ഞെടുക്കുക",

        grievanceLetter: "പരാതിക്കത്ത്",
        photoOrScan: "കൈയെഴുത്തിലോ അച്ചടിച്ചോ ഉള്ള കത്തിന്റെ ഫോട്ടോ അല്ലെങ്കിൽ സ്കാൻ",
        chooseFile: "ഫയൽ തിരഞ്ഞെടുക്കാൻ ക്ലിക്ക് ചെയ്യുക അല്ലെങ്കിൽ ഇവിടെ ഇടുക",
        supportedFiles: "JPG, PNG, WEBP അല്ലെങ്കിൽ PDF, പരമാവധി 10 MB",
        processWithAI: "AI ഉപയോഗിച്ച് പരിശോധിക്കുക",
        readingLetter: "പരാതിക്കത്ത് വായിക്കുന്നു...",
        processingInfo:
            "AI നിങ്ങളുടെ രേഖ വായിക്കുകയാണ്. ലാപ്‌ടോപ്പിൽ ഇത് 1-3 മിനിറ്റ് വരെ എടുത്തേക്കാം.",

        chatbotTitle: "കേരള സഹായി",
        chatbotWelcome:
            "നമസ്കാരം! കേരളത്തെയും സർക്കാർ സേവനങ്ങളെയും കുറിച്ച് എന്തും ചോദിക്കാം.",
        chatbotSubtitle: "ഔദ്യോഗിക വെബ് പേജുകളിൽ നിന്നുള്ള ഉത്തരങ്ങൾ",
        chatPlaceholder: "കേരളത്തെക്കുറിച്ച് ഒരു ചോദ്യം ചോദിക്കൂ...",
        send: "അയയ്ക്കുക",
        sources: "വിവര സ്രോതസ്സുകൾ",
        closeChat: "ചാറ്റ് അടയ്ക്കുക",
        openChat: "ചാറ്റ് തുറക്കുക",

        language: "ഭാഷ",
        english: "English",
        malayalam: "മലയാളം",

        selectFileError: "ദയവായി ഒരു ഫയൽ തിരഞ്ഞെടുക്കുക.",
        unsupportedFile: "പിന്തുണയ്ക്കാത്ത ഫയൽ ഫോർമാറ്റ്.",
        uploadError: "അപ്‌ലോഡ് ചെയ്ത ഫയൽ പരിശോധിക്കാൻ കഴിഞ്ഞില്ല.",
        apiError: "ബാക്ക്‌എൻഡ് പ്രവർത്തിക്കുന്നുണ്ടോ എന്ന് പരിശോധിക്കുക.",
    },
};

export function LanguageProvider({ children }) {
    const [language, setLanguageState] = useState(() => {
        const savedLanguage = localStorage.getItem("website-language");

        return savedLanguage === "ml" ? "ml" : "en";
    });

    function setLanguage(newLanguage) {
        if (newLanguage !== "en" && newLanguage !== "ml") {
            return;
        }

        setLanguageState(newLanguage);
        localStorage.setItem("website-language", newLanguage);
    }

    function t(key) {
        return (
            translations[language][key] ??
            translations.en[key] ??
            key
        );
    }

    useEffect(() => {
        document.documentElement.lang = language;
    }, [language]);

    return (
        <LanguageContext.Provider
            value={{ language, setLanguage, t }}
        >
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const context = useContext(LanguageContext);

    if (!context) {
        throw new Error(
            "useLanguage must be used inside LanguageProvider"
        );
    }

    return context;
}
