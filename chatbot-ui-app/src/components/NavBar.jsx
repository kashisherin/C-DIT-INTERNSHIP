import { NavLink } from "react-router";

// NavLink knows whether its page is open, so we can highlight it
function linkStyle({ isActive }) {
    return isActive
        ? "rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white"
        : "rounded-lg px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100";
}

export default function NavBar() {
    return (
        <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
            <div>
                <h1 className="text-xl font-bold text-gray-800">
                    Grievance Portal
                </h1>

                <p className="text-sm text-gray-500">
                    AI-assisted grievance processing
                </p>
            </div>

            <div className="flex items-center gap-3">
                <NavLink to="/citizen" className={linkStyle}>
                    Citizen
                </NavLink>

                <NavLink to="/official" className={linkStyle}>
                    Official
                </NavLink>
            </div>
        </nav>
    );
}