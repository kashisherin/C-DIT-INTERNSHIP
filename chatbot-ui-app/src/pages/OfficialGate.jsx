import { useEffect, useState } from "react";
import {
    getOfficialSession,
    loginOfficial,
    logoutOfficial,
} from "../api";
import OfficialPage from "./OfficialPage";
import OfficialDatabasePage from "./OfficialDatabasePage";

export default function OfficialGate({ databaseMode = false }) {
    const [authenticated, setAuthenticated] = useState(false);
    const [checking, setChecking] = useState(true);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    // Check whether an official session already exists.
    useEffect(() => {
        let active = true;

        getOfficialSession()
            .then((data) => {
                if (active) {
                    setUsername(data.username);
                    setAuthenticated(true);
                }
            })
            .catch(() => {
                if (active) {
                    setAuthenticated(false);
                }
            })
            .finally(() => {
                if (active) {
                    setChecking(false);
                }
            });

        return () => {
            active = false;
        };
    }, []);

    // Official login.
    async function handleLogin(event) {
        event.preventDefault();

        if (busy) return;

        setBusy(true);
        setError("");

        try {
            const result = await loginOfficial(
                username.trim(),
                password
            );

            setUsername(result.username);
            setPassword("");
            setAuthenticated(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    // Official logout.
    async function handleLogout() {
        try {
            await logoutOfficial();
            setAuthenticated(false);
            setPassword("");
            setError("");
        } catch (err) {
            setError(err.message);
        }
    }

    // Session verification screen.
    if (checking) {
        return (
            <main className="flex min-h-[70vh] items-center justify-center bg-slate-50">
                <p className="text-gray-600">
                    Checking official session...
                </p>
            </main>
        );
    }

    // Display the Official Portal only after authentication.
    if (authenticated) {
        return (
            <>
                {error && (
                    <div
                        role="alert"
                        className="bg-red-50 px-4 py-2 text-center text-sm text-red-700"
                    >
                        {error}
                    </div>
                )}

                {databaseMode ? (
                    <OfficialDatabasePage username={username} />
                ) : (
                    <OfficialPage
                        onLogout={handleLogout}
                        username={username}
                    />
                )}
            </>
        );
    }

    // Official login screen.
    return (
        <main className="flex min-h-[calc(100vh-73px)] items-center justify-center bg-slate-50 px-4 py-10">

            <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 shadow-lg">

                <div className="mb-7 text-center">

                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-3xl">
                        🏛️
                    </div>

                    <h1 className="text-2xl font-bold text-gray-800">
                        Official Login
                    </h1>

                    <p className="mt-2 text-sm text-gray-500">
                        Sign in to access the Grievance Management Portal.
                    </p>

                </div>

                <form onSubmit={handleLogin} className="space-y-5">

                    <div>
                        <label
                            htmlFor="official-username"
                            className="mb-1 block text-sm font-semibold text-gray-700"
                        >
                            Username
                        </label>

                        <input
                            id="official-username"
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(event.target.value)
                            }
                            autoComplete="username"
                            required
                            disabled={busy}
                            placeholder="Enter official username"
                            className="w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
                        />
                    </div>

                    <div>
                        <label
                            htmlFor="official-password"
                            className="mb-1 block text-sm font-semibold text-gray-700"
                        >
                            Password
                        </label>

                        <input
                            id="official-password"
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            autoComplete="current-password"
                            required
                            disabled={busy}
                            placeholder="Enter your password"
                            className="w-full rounded-xl border border-gray-300 px-4 py-3 text-gray-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
                        />
                    </div>

                    {error && (
                        <div
                            role="alert"
                            className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
                        >
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={busy || !username.trim() || !password}
                        className="w-full rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
                    >
                        {busy ? "Signing in..." : "Sign In"}
                    </button>

                </form>

                <p className="mt-6 text-center text-xs text-gray-400">
                    Authorized officials only
                </p>

            </div>

        </main>
    );
}