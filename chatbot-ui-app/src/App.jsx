import { Route, Routes } from "react-router";
import NavBar from "./components/NavBar";
import ChatWidget from "./components/ChatWidget";
import CitizenPage from "./pages/CitizenPage";
import OfficialPage from "./pages/OfficialPage";

export default function App() {
    return (
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

            {/* The chat button floats on top of every page */}
            <ChatWidget />
        </div>
    );
}