import { Route, Routes } from "react-router";
import NavBar from "./components/NavBar";
import ChatWidget from "./components/ChatWidget";
import CitizenPage from "./pages/CitizenPage";
import OfficialPage from "./pages/OfficialPage";
import { LanguageProvider } from "./context/LanguageContext";

export default function App() {
    return (
        <LanguageProvider>
            <div className="min-h-screen bg-gray-100">
                <NavBar />

                <Routes>
                    <Route path="/" element={<CitizenPage />} />
                    <Route path="/official" element={<OfficialPage />} />
                    <Route
                        path="*"
                        element={<p className="p-8">Page not found.</p>}
                    />
                </Routes>

                <ChatWidget />
            </div>
        </LanguageProvider>
    );
}