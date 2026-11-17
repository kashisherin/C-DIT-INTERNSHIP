import { Route, Routes } from "react-router";
import NavBar from "./components/NavBar";
import ChatWidget from "./components/ChatWidget";
import CitizenPage from "./pages/CitizenPage";
import OfficialGate from "./pages/OfficialGate";
import { LanguageProvider } from "./context/LanguageContext";

export default function App() {
    return (
        <LanguageProvider>
            <div className="min-h-screen bg-gray-100">
                <NavBar />

                <Routes>
                    {/* Citizen Portal */}
                    <Route
                        path="/"
                        element={
                            <>
                                <CitizenPage />
                                <ChatWidget />
                            </>
                        }
                    />

                    {/* Official AI Assistant */}
                    <Route
                        path="/official"
                        element={<OfficialGate />}
                    />

                    {/* Separate, Official-authenticated Database Management page */}
                    <Route
                        path="/official/database"
                        element={<OfficialGate databaseMode />}
                    />

                    {/* Invalid routes */}
                    <Route
                        path="*"
                        element={<p className="p-8">Page not found.</p>}
                    />
                </Routes>
            </div>
        </LanguageProvider>
    );
}
