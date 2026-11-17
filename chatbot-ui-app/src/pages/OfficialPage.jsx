
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { askOfficialQuestion,updateGrievanceStatus, } from "../api";
import { useLanguage } from "../context/LanguageContext";

const API_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    
export default function OfficialPage({ onLogout, username }) {
    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    const welcomeMessage = isMalayalam
        ? "നമസ്കാരം! രജിസ്റ്റർ ചെയ്ത പരാതികൾ തിരയാനും വകുപ്പുതല വിവരങ്ങൾ പരിശോധിക്കാനും എന്നോട് ചോദിക്കാം."
        : "Welcome, Official. I can help you retrieve registered grievances, search departments and view individual complaint records.";

    const [messages, setMessages] = useState([
        {
            role: "assistant",
            text: welcomeMessage,
        },
    ]);

    const [history, setHistory] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const bottomRef = useRef(null);
    const inputRef = useRef(null);

    // Update the welcome message when the language changes.
    useEffect(() => {
        setMessages((previous) => {
            if (
                previous.length === 1 &&
                previous[0].role === "assistant"
            ) {
                return [
                    {
                        role: "assistant",
                        text: welcomeMessage,
                    },
                ];
            }

            return previous;
        });
    }, [welcomeMessage]);

    // Automatically scroll to the newest conversation.
    useEffect(() => {
        bottomRef.current?.scrollIntoView({
            behavior: "smooth",
        });
    }, [messages, loading]);

    // Send the official's question to the backend.
    async function handleSend(question) {
        question = question.trim();

        if (!question || loading) return;

        setMessages((previous) => [
            ...previous,
            {
                role: "user",
                text: question,
            },
        ]);

        const updatedHistory = [
            ...history.map((message) => ({
                ...message,
                content: String(message.content || "").slice(0, 3500),
            })),
            {
                role: "user",
                content: question.slice(0, 3500),
            },
        ].slice(-10);

        setInput("");
        setLoading(true);

        try {
            const result = await askOfficialQuestion(
                question,
                updatedHistory
            );

            setMessages((previous) => [
                ...previous,
                {
                    role: "assistant",
                    text: result.reply,
                    action: result.action,
                    data: result.data,
                    count: result.count,
                },
            ]);

            // Preserve compact database information for follow-up questions.
            const historyData = Array.isArray(result.data)
                ? result.data.slice(0, 10).map((record) => ({
                    grievance_id: record.grievance_id,
                    department_code: record.department_code,
                    department_slot: record.department_slot,
                    citizen_name: (record.citizen_name || "").slice(0, 80),
                    status: record.status,
                }))
                : result.data && typeof result.data === "object"
                    ? {
                        total: result.data.total,
                        departments: result.data.departments,
                        grievance_id: result.data.grievance_id,
                        department_code: result.data.department_code,
                        department_slot: result.data.department_slot,
                        citizen_name: result.data.citizen_name,
                        status: result.data.status,
                    }
                    : null;

            const assistantContext = [
                (result.reply || "").slice(0, 1000),
                historyData
                    ? `Retrieved grievance records: ${JSON.stringify(historyData)}`
                    : "",
            ]
                .filter(Boolean)
                .join("\n\n")
                .slice(0, 3500);

            setHistory([
                ...updatedHistory,
                {
                    role: "assistant",
                    content: assistantContext,
                },
            ].slice(-10));

        } catch (error) {
            setMessages((previous) => [
                ...previous,
                {
                    role: "error",
                    text: error.message,
                },
            ]);

        } finally {
            setLoading(false);
            inputRef.current?.focus();
        }
    }

    function handleSubmit(event) {
        event.preventDefault();
        handleSend(input);
    }

    function clearConversation() {
        if (loading) return;

        setMessages([
            {
                role: "assistant",
                text: welcomeMessage,
            },
        ]);

        setHistory([]);
    }

    const suggestions = isMalayalam
        ? [
            "ആകെ എത്ര പരാതികൾ രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്?",
            "KSRTC-യിൽ രജിസ്റ്റർ ചെയ്ത പരാതികൾ കാണിക്കുക",
            "KSEB-യിലെ പരാതികൾ കാണിക്കുക",
        ]
        : [
            "How many grievances are registered?",
            "Show all grievances registered under KSRTC",
            "Show all KSEB grievances",
        ];

    return (
        <main className="flex h-[calc(100vh-73px)] min-h-[540px] flex-col bg-slate-50">

            {/* Official portal header */}
            <header className="flex items-center justify-between border-b border-gray-200 bg-white px-5 py-4 sm:px-8">

                <div>
                    <h1 className="text-xl font-bold text-gray-800">
                        {isMalayalam ? "ഔദ്യോഗിക പരാതി സഹായി" : "Official Grievance Assistant"}
                    </h1>

                    <p className="mt-1 text-xs text-gray-500">
                        {isMalayalam
                            ? "വകുപ്പുതല പരാതി വിവരങ്ങൾ"
                            : "Central grievance management and retrieval"}
                    </p>
                </div>

                <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
                    <span className="hidden text-sm text-gray-500 sm:block">
                        {username}
                    </span>

                    <Link
                        to="/official/database"
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                        {isMalayalam ? "ഡാറ്റാബേസ് മാനേജ്മെന്റ്" : "Database Management"}
                    </Link>

                    <button
                        type="button"
                        onClick={clearConversation}
                        disabled={loading}
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 disabled:opacity-50"
                    >
                        {isMalayalam ? "ചാറ്റ് മായ്ക്കുക" : "Clear chat"}
                    </button>

                    <button
                        type="button"
                        onClick={onLogout}
                        className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
                    >
                        {isMalayalam ? "പുറത്തുകടക്കുക" : "Logout"}
                    </button>
                </div>

            </header>

            {/* Conversation area */}
            <section className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">

                <div className="mx-auto max-w-5xl space-y-6">

                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${
                                message.role === "user"
                                    ? "justify-end"
                                    : "justify-start"
                            }`}
                        >
                            <div
                                className={`w-full max-w-[90%] sm:max-w-[85%] ${
                                    message.role === "user"
                                        ? "rounded-2xl rounded-br-sm bg-blue-600 p-4 text-white"
                                        : message.role === "error"
                                            ? "rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700"
                                            : "space-y-3"
                                }`}
                            >
                                <div
                                    className={
                                        message.role === "assistant"
                                            ? "rounded-2xl rounded-bl-sm border border-gray-200 bg-white p-4 text-gray-800 shadow-sm"
                                            : ""
                                    }
                                >
                                    <p className="whitespace-pre-wrap leading-relaxed">
                                        {message.text}
                                    </p>
                                </div>

                                {message.role === "assistant" &&
                                    message.data !== undefined && (
                                        <OfficialDataView
                                            data={message.data}
                                            count={message.count}
                                            language={language}
                                        />
                                    )}
                            </div>
                        </div>
                    ))}

                    {/* Loading indicator */}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
                                <div className="flex gap-2">
                                    {[0, 150, 300].map((delay) => (
                                        <span
                                            key={delay}
                                            style={{
                                                animationDelay: `${delay}ms`,
                                            }}
                                            className="h-2.5 w-2.5 animate-bounce rounded-full bg-blue-500"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={bottomRef} />

                </div>
            </section>

            {/* Example questions */}
            {messages.length === 1 && !loading && (
                <div className="border-t border-gray-200 bg-white px-4 py-4 sm:px-8">
                    <div className="mx-auto max-w-5xl">
                        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                            {isMalayalam
                                ? "ഉദാഹരണ ചോദ്യങ്ങൾ"
                                : "Suggested questions"}
                        </p>

                        <div className="flex flex-wrap gap-2">
                            {suggestions.map((suggestion) => (
                                <button
                                    key={suggestion}
                                    type="button"
                                    onClick={() => handleSend(suggestion)}
                                    className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-left text-sm text-gray-700 transition hover:border-blue-400 hover:bg-blue-50"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Message input */}
            <form
                onSubmit={handleSubmit}
                className="border-t border-gray-200 bg-white p-4 sm:px-8 sm:py-5"
            >
                <div className="mx-auto flex max-w-5xl gap-3">

                    <input
                        ref={inputRef}
                        type="text"
                        value={input}
                        onChange={(event) =>
                            setInput(event.target.value)
                        }
                        disabled={loading}
                        placeholder={
                            isMalayalam
                                ? "പരാതികളെക്കുറിച്ച് ചോദിക്കൂ..."
                                : "Ask about registered grievances..."
                        }
                        className="min-w-0 flex-1 rounded-xl border border-gray-300 px-4 py-3 text-gray-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
                    />

                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
                    >
                        {isMalayalam ? "അയയ്ക്കുക" : "Send"}
                    </button>

                </div>

                <p className="mx-auto mt-2 max-w-5xl text-center text-xs text-gray-400">
                    {isMalayalam
                        ? "പരാതി ഡാറ്റാബേസിൽ നിന്നുള്ള വിവരങ്ങൾ ഉപയോഗിച്ചാണ് ഉത്തരങ്ങൾ തയ്യാറാക്കുന്നത്."
                        : "Answers are retrieved from the registered grievance database."}
                </p>
            </form>

        </main>
    );
}


// ============================================================
// DISPLAY ACTUAL DATABASE RESULTS
// ============================================================

function OfficialDataView({ data, count, language }) {
    const isMalayalam = language === "ml";
        const [selectedStatus, setSelectedStatus] = useState(
        data?.status || "REGISTERED"
    );
    const [currentStatus, setCurrentStatus] = useState(
        data?.status || "REGISTERED"
    );
    const [statusBusy, setStatusBusy] = useState(false);
    const [statusMessage, setStatusMessage] = useState("");
    const [showStatusSecurity, setShowStatusSecurity] = useState(false);
    const [statusSecurityPassword, setStatusSecurityPassword] = useState("");
    const [statusSecurityError, setStatusSecurityError] = useState("");

    useEffect(() => {
        const status = data?.status || "REGISTERED";

        setSelectedStatus(status);
        setCurrentStatus(status);
        setStatusMessage("");
    }, [data?.grievance_id, data?.status]);
    const labels = {
        slot: isMalayalam ? "സ്ലോട്ട്" : "Slot",
        name: isMalayalam ? "പൗരന്റെ പേര്" : "Citizen name",
        id: isMalayalam ? "രജിസ്ട്രേഷൻ ID" : "Registration ID",
        department: isMalayalam ? "വകുപ്പ്" : "Department",
        status: isMalayalam ? "നില" : "Status",
        summary: isMalayalam ? "സംഗ്രഹം" : "Summary",
        description: isMalayalam ? "വിശദീകരണം" : "Description",
        date: isMalayalam ? "രജിസ്റ്റർ ചെയ്ത തീയതി" : "Registered date",
        reason: isMalayalam ? "വകുപ്പ് നിർദ്ദേശിച്ചതിന്റെ കാരണം" : "Department reason",
        original: isMalayalam ? "മൂലരേഖ തുറക്കുക" : "Open original document",
        noName: isMalayalam ? "പേര് ലഭ്യമല്ല" : "Name not available",
        noRecords: isMalayalam ? "രേഖകൾ ഒന്നും കണ്ടെത്തിയില്ല." : "No records found.",
    };

    function handleStatusUpdate() {
        if (!data?.grievance_id || statusBusy) return;
        setStatusSecurityPassword("");
        setStatusSecurityError("");
        setShowStatusSecurity(true);
    }

    async function confirmStatusUpdate(event) {
        event.preventDefault();
        if (!data?.grievance_id || statusBusy || !statusSecurityPassword) return;

        setStatusBusy(true);
        setStatusMessage("");
        setStatusSecurityError("");

        try {
            const result = await updateGrievanceStatus(
                data.grievance_id,
                selectedStatus,
                statusSecurityPassword
            );

            setSelectedStatus(result.status);
            setCurrentStatus(result.status);
            setShowStatusSecurity(false);
            setStatusSecurityPassword("");

            setStatusMessage(
                isMalayalam
                    ? "പരാതിയുടെ നില വിജയകരമായി പുതുക്കി."
                    : "Grievance status updated successfully."
            );

        } catch (error) {
            setStatusSecurityError(error.message);

        } finally {
            setStatusBusy(false);
        }
    }

    if (data === null || data === undefined) {
        return null;
    }

    // Department-wise and total counts.
    if (data && Array.isArray(data.departments)) {
        return (
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">

                <div className="mb-4 rounded-lg bg-blue-50 p-4">
                    <p className="text-sm text-blue-700">
                        {isMalayalam
                            ? "ആകെ രജിസ്റ്റർ ചെയ്ത പരാതികൾ"
                            : "Total registered grievances"}
                    </p>

                    <p className="mt-1 text-3xl font-bold text-blue-800">
                        {data.total}
                    </p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-gray-50 text-gray-600">
                            <tr>
                                <th className="p-3">{labels.department}</th>
                                <th className="p-3 text-right">Count</th>
                            </tr>
                        </thead>

                        <tbody>
                            {data.departments.map((item) => (
                                <tr
                                    key={item.department_code}
                                    className="border-t border-gray-100"
                                >
                                    <td className="p-3 font-medium">
                                        {item.department_code}
                                    </td>
                                    <td className="p-3 text-right">
                                        {item.total}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </div>
        );
    }

    // Lists and search results.
    if (Array.isArray(data)) {
        if (data.length === 0) {
            return (
                <div className="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-500">
                    {labels.noRecords}
                </div>
            );
        }

        return (
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">

                <div className="border-b border-gray-200 px-4 py-3">
                    <p className="font-semibold text-gray-800">
                        {isMalayalam
                            ? `കണ്ടെത്തിയ രേഖകൾ: ${count ?? data.length}`
                            : `Retrieved records: ${count ?? data.length}`}
                    </p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full min-w-[750px] text-left text-sm">
                        <thead className="bg-gray-50 text-gray-600">
                            <tr>
                                <th className="p-3">{labels.slot}</th>
                                <th className="p-3">{labels.name}</th>
                                <th className="p-3">{labels.id}</th>
                                <th className="p-3">{labels.department}</th>
                                <th className="p-3">{labels.status}</th>
                            </tr>
                        </thead>

                        <tbody>
                            {data.map((record) => (
                                <tr
                                    key={record.grievance_id}
                                    className="border-t border-gray-100 hover:bg-gray-50"
                                >
                                    <td className="p-3">
                                        {record.department_slot}
                                    </td>
                                    <td className="p-3">
                                        {record.citizen_name || labels.noName}
                                    </td>
                                    <td className="p-3 font-medium text-blue-700">
                                        {record.grievance_id}
                                    </td>
                                    <td className="p-3">
                                        {record.department_code}
                                    </td>
                                    <td className="p-3">
                                        {record.status}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

            </div>
        );
    }

    // Complete details of an individual grievance.
    if (data && data.grievance_id) {
        return (
            <div className="space-y-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">

                <div className="grid gap-3 sm:grid-cols-2">

                    <Detail
                        label={labels.id}
                        value={data.grievance_id}
                    />

                    <Detail
                        label={labels.slot}
                        value={data.department_slot}
                    />

                    <Detail
                        label={labels.name}
                        value={data.citizen_name || labels.noName}
                    />

                    <Detail
                        label={labels.department}
                        value={data.department_code}
                    />

                    <Detail
                        label={labels.status}
                        value={currentStatus}
                    />

                    <Detail
                        label={labels.date}
                        value={data.registered_at}
                    />

                </div>

                <div className="rounded-lg bg-blue-50 p-4">
                    <h3 className="mb-2 font-semibold text-blue-800">
                        {labels.summary}
                    </h3>
                    <p className="whitespace-pre-wrap text-sm text-gray-800">
                        {data.summary}
                    </p>
                </div>

                <div className="rounded-lg bg-gray-50 p-4">
                    <h3 className="mb-2 font-semibold text-gray-800">
                        {labels.description}
                    </h3>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                        {data.description}
                    </p>
                </div>

                {data.department_reason && (
                    <div className="rounded-lg border border-gray-200 p-4">
                        <h3 className="mb-2 font-semibold text-gray-800">
                            {labels.reason}
                        </h3>
                        <p className="text-sm text-gray-700">
                            {data.department_reason}
                        </p>
                    </div>
                )}

                                {/* Grievance status management */}
                <div className="rounded-xl border border-gray-200 bg-white p-4">

                    <h3 className="mb-3 font-semibold text-gray-800">
                        {isMalayalam
                            ? "പരാതിയുടെ നിലവാരം പുതുക്കുക"
                            : "Update Grievance Status"}
                    </h3>

                    <div className="flex flex-col gap-3 sm:flex-row">

                        <select
                            value={selectedStatus}
                            onChange={(event) => {
                                setSelectedStatus(event.target.value);
                                setStatusMessage("");
                            }}
                            disabled={statusBusy}
                            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-800 outline-none focus:border-blue-500"
                        >
                            <option value="REGISTERED">REGISTERED</option>
                            <option value="UNDER_REVIEW">UNDER_REVIEW</option>
                            <option value="IN_PROGRESS">IN_PROGRESS</option>
                            <option value="RESOLVED">RESOLVED</option>
                            <option value="REJECTED">REJECTED</option>
                            <option value="CLOSED">CLOSED</option>
                        </select>

                        <button
                            type="button"
                            onClick={handleStatusUpdate}
                            disabled={
                                statusBusy ||
                                selectedStatus === currentStatus
                            }
                            className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
                        >
                            {statusBusy
                                ? (isMalayalam ? "പുതുക്കുന്നു..." : "Updating...")
                                : (isMalayalam ? "നില പുതുക്കുക" : "Update Status")}
                        </button>

                    </div>

                    {statusMessage && (
                        <p className="mt-3 text-sm text-gray-600">
                            {statusMessage}
                        </p>
                    )}
                </div>

                {showStatusSecurity && (
                    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4">
                        <form onSubmit={confirmStatusUpdate} className="w-full max-w-md space-y-4 rounded-xl bg-white p-6 shadow-2xl">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">
                                    {isMalayalam ? "രണ്ടാം സുരക്ഷാ പരിശോധന" : "Second Security Verification"}
                                </h3>
                                <p className="mt-1 text-sm text-gray-600">
                                    {isMalayalam
                                        ? "പരാതിയുടെ നില മാറ്റാൻ പ്രത്യേക സുരക്ഷാ പാസ്‌വേഡ് നൽകുക."
                                        : "Enter the separate edit/delete security password to change this grievance status."}
                                </p>
                            </div>
                            <label className="block text-sm font-medium text-gray-700">
                                {isMalayalam ? "സുരക്ഷാ പാസ്‌വേഡ്" : "Security password"}
                                <input type="password" autoComplete="current-password" autoFocus required
                                    value={statusSecurityPassword}
                                    onChange={(event) => setStatusSecurityPassword(event.target.value)}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            {statusSecurityError && (
                                <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                                    {statusSecurityError}
                                </p>
                            )}
                            <div className="flex justify-end gap-2">
                                <button type="button" onClick={() => setShowStatusSecurity(false)} disabled={statusBusy}
                                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700">
                                    {isMalayalam ? "റദ്ദാക്കുക" : "Cancel"}
                                </button>
                                <button type="submit" disabled={statusBusy || !statusSecurityPassword}
                                    className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
                                    {statusBusy
                                        ? (isMalayalam ? "പരിശോധിക്കുന്നു..." : "Verifying...")
                                        : (isMalayalam ? "സ്ഥിരീകരിക്കുക" : "Verify and update")}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {data.document_url && (
                    <a
                        href={`${API_URL}${data.document_url}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                    >
                        {labels.original}
                    </a>
                )}

            </div>
        );
    }

    return null;
}


function Detail({ label, value }) {
    return (
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
            <p className="text-xs text-gray-500">
                {label}
            </p>

            <p className="mt-1 break-words text-sm font-semibold text-gray-800">
                {value ?? "—"}
            </p>
        </div>
    );
}
