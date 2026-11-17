import { useEffect, useMemo, useRef, useState } from "react";
import {
    clearAllGrievances,
    deleteFilteredGrievances,
    deleteSelectedGrievances,
    getDatabaseManagementSession,
    getManagementGrievances,
    getManagementSummary,
    loginDatabaseManagement,
    logoutDatabaseManagement,
    updateManagementGrievance,
} from "../api";
import { useLanguage } from "../context/LanguageContext";

const DEPARTMENTS = [
    "KWA", "KSEB", "PWD", "LSGD", "REVENUE", "POLICE",
    "HEALTH", "EDUCATION", "CIVIL_SUPPLIES", "SOCIAL_JUSTICE",
    "TRANSPORT", "OTHER",
];

const STATUSES = [
    "REGISTERED", "UNDER_REVIEW", "IN_PROGRESS",
    "RESOLVED", "REJECTED", "CLOSED",
];

const EMPTY_FILTERS = {
    department_code: "",
    status: "",
    search: "",
    date_from: "",
    date_to: "",
};

const EMPTY_EDIT = {
    citizen_name: "",
    summary: "",
    description: "",
    department_reason: "",
    status: "REGISTERED",
};

export default function DatabaseManagementPage() {
    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    const [managerAuthChecking, setManagerAuthChecking] = useState(true);
    const [managerAuthenticated, setManagerAuthenticated] = useState(false);
    const [managerCredentials, setManagerCredentials] = useState({ username: "", password: "" });
    const [managerLoginBusy, setManagerLoginBusy] = useState(false);
    const [managerLoginError, setManagerLoginError] = useState("");
    const [securityTitle, setSecurityTitle] = useState("");
    const [securityPassword, setSecurityPassword] = useState("");
    const [securityError, setSecurityError] = useState("");
    const [securityBusy, setSecurityBusy] = useState(false);
    const pendingSecurityAction = useRef(null);

    const [filters, setFilters] = useState(EMPTY_FILTERS);
    const [records, setRecords] = useState([]);
    const [summary, setSummary] = useState({ total: 0, departments: [] });
    const [selected, setSelected] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");
    const [editing, setEditing] = useState(null);
    const [editForm, setEditForm] = useState(EMPTY_EDIT);
    const [clearPhrase, setClearPhrase] = useState("");
    const [showClear, setShowClear] = useState(false);

    const text = useMemo(() => isMalayalam ? {
        title: "ഡാറ്റാബേസ് മാനേജ്മെന്റ്",
        subtitle: "രജിസ്റ്റർ ചെയ്ത പരാതികളും അവയുടെ രേഖകളും നിയന്ത്രിക്കുക.",
        total: "ആകെ പരാതികൾ",
        search: "പേര്, പരാതി ID അല്ലെങ്കിൽ സംഗ്രഹം തിരയുക",
        department: "വകുപ്പ്",
        allDepartments: "എല്ലാ വകുപ്പുകളും",
        status: "നില",
        allStatuses: "എല്ലാ നിലകളും",
        from: "തീയതി മുതൽ",
        to: "തീയതി വരെ",
        apply: "ഫിൽട്ടർ ചെയ്യുക",
        refresh: "പുതുക്കുക",
        select: "തിരഞ്ഞെടുക്കുക",
        id: "പരാതി ID",
        name: "പൗരന്റെ പേര്",
        slot: "സ്ലോട്ട്",
        registered: "രജിസ്റ്റർ ചെയ്ത തീയതി",
        actions: "പ്രവർത്തനങ്ങൾ",
        edit: "തിരുത്തുക",
        delete: "മായ്ക്കുക",
        selectedDelete: "തിരഞ്ഞെടുത്തവ മായ്ക്കുക",
        filteredDelete: "ഫിൽട്ടർ ചെയ്തവ മായ്ക്കുക",
        clearAll: "എല്ലാ പരാതികളും മായ്ക്കുക",
        noRecords: "പരാതികൾ കണ്ടെത്തിയില്ല.",
        editTitle: "പരാതി തിരുത്തുക",
        summary: "സംഗ്രഹം",
        description: "പൂർണ്ണ വിവരണം",
        reason: "വകുപ്പ് നിർദ്ദേശിച്ചതിന്റെ കാരണം",
        save: "മാറ്റങ്ങൾ സംരക്ഷിക്കുക",
        cancel: "റദ്ദാക്കുക",
        confirmClear: "സ്ഥിരീകരിക്കാൻ DELETE ALL GRIEVANCES എന്ന് ടൈപ്പ് ചെയ്യുക.",
        clearWarning: "ഇത് എല്ലാ പരാതികളും അവയുടെ അപ്‌ലോഡ് ചെയ്ത രേഖകളും സ്ഥിരമായി മായ്ക്കും. ഈ നടപടി തിരിച്ചെടുക്കാനാവില്ല.",
        confirm: "സ്ഥിരീകരിച്ച് മായ്ക്കുക",
        close: "അടയ്ക്കുക",
        loading: "ലോഡ് ചെയ്യുന്നു...",
        saved: "പരാതി വിജയകരമായി പുതുക്കി.",
        deleted: "തിരഞ്ഞെടുത്ത ഡാറ്റ മായ്ച്ചു.",
        cleared: "എല്ലാ പരാതികളും മായ്ച്ചു.",
        count: "കാണിക്കുന്ന രേഖകൾ",
        immutable: "പരാതി ID, വകുപ്പ്, സ്ലോട്ട് എന്നിവ രേഖയുടെ തിരിച്ചറിയൽ നിലനിർത്താൻ മാറ്റാനാവില്ല.",
        chooseFilter: "ഫിൽട്ടർ ഉപയോഗിച്ചുള്ള മായ്ക്കലിന് വകുപ്പ്, നില അല്ലെങ്കിൽ തീയതി തിരഞ്ഞെടുക്കുക.",
        loginTitle: "ഡാറ്റാബേസ് മാനേജ്മെന്റ് ലോഗിൻ",
        loginDescription: "ഡാറ്റാബേസ് മാനേജ്മെന്റിലേക്ക് പ്രവേശിക്കാൻ പ്രത്യേക അക്കൗണ്ട് ഉപയോഗിച്ച് ലോഗിൻ ചെയ്യുക.",
        username: "ഉപയോക്തൃനാമം",
        password: "പാസ്‌വേഡ്",
        login: "ലോഗിൻ ചെയ്യുക",
        logoutManager: "ഡാറ്റാബേസ് ലോഗ്ഔട്ട്",
        authChecking: "പ്രാമാണീകരണം പരിശോധിക്കുന്നു...",
        secondAuthTitle: "രണ്ടാം സുരക്ഷാ പരിശോധന",
        secondAuthDescription: "ഈ മാറ്റം നടത്താൻ പ്രത്യേക എഡിറ്റ്/ഡിലീറ്റ് സുരക്ഷാ പാസ്‌വേഡ് നൽകുക.",
        confirmAction: "സ്ഥിരീകരിച്ച് തുടരുക",
        actionPassword: "എഡിറ്റ്/ഡിലീറ്റ് സുരക്ഷാ പാസ്‌വേഡ്",
    } : {
        title: "Database Management",
        subtitle: "View, edit and remove registered grievances and their uploaded documents.",
        total: "Total grievances",
        search: "Search name, grievance ID or summary",
        department: "Department",
        allDepartments: "All departments",
        status: "Status",
        allStatuses: "All statuses",
        from: "Registered from",
        to: "Registered to",
        apply: "Apply filters",
        refresh: "Refresh",
        select: "Select",
        id: "Grievance ID",
        name: "Citizen name",
        slot: "Slot",
        registered: "Registered at",
        actions: "Actions",
        edit: "Edit",
        delete: "Delete",
        selectedDelete: "Delete selected",
        filteredDelete: "Delete filtered records",
        clearAll: "Clear all grievances",
        noRecords: "No grievance records found.",
        editTitle: "Edit grievance",
        summary: "Summary",
        description: "Full description",
        reason: "Department reason",
        save: "Save changes",
        cancel: "Cancel",
        confirmClear: "Type DELETE ALL GRIEVANCES to confirm.",
        clearWarning: "This permanently deletes every grievance record and its associated uploaded documents. This cannot be undone.",
        confirm: "Confirm and clear all",
        close: "Close",
        loading: "Loading...",
        saved: "Grievance updated successfully.",
        deleted: "Selected records deleted.",
        cleared: "All grievance records cleared.",
        count: "Records shown",
        immutable: "Grievance ID, department and slot are kept fixed to preserve record identity.",
        chooseFilter: "Choose a department, status or date range before deleting filtered records.",
        loginTitle: "Database Management Login",
        loginDescription: "Enter the separate Database Management account to unlock this section.",
        username: "Database username",
        password: "Database password",
        login: "Unlock Database Management",
        logoutManager: "Database Logout",
        authChecking: "Checking Database Management session...",
        secondAuthTitle: "Second Security Verification",
        secondAuthDescription: "Enter the separate edit/delete security password to authorize this change.",
        confirmAction: "Verify and continue",
        actionPassword: "Edit/delete security password",
    }, [isMalayalam]);

    async function loadData(nextFilters = filters) {
        setLoading(true);
        setError("");
        try {
            const [listResult, summaryResult] = await Promise.all([
                getManagementGrievances({ ...nextFilters, limit: 500, offset: 0 }),
                getManagementSummary(),
            ]);
            setRecords(listResult.grievances || []);
            setSummary(summaryResult || { total: 0, departments: [] });
            setSelected([]);
        } catch (requestError) {
            const message = requestError.message || "Unable to load grievance records.";
            setError(message);
            if (message.includes("Separate Database Management login required.")) {
                setManagerAuthenticated(false);
            }
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        let active = true;
        getDatabaseManagementSession()
            .then(() => {
                if (active) setManagerAuthenticated(true);
            })
            .catch(() => {
                if (active) setManagerAuthenticated(false);
            })
            .finally(() => {
                if (active) setManagerAuthChecking(false);
            });
        return () => { active = false; };
    }, []);

    useEffect(() => {
        if (managerAuthenticated) {
            loadData(EMPTY_FILTERS);
        }
        // Reload only after a successful separate Database Management login.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [managerAuthenticated]);

    async function handleManagerLogin(event) {
        event.preventDefault();
        setManagerLoginBusy(true);
        setManagerLoginError("");
        try {
            await loginDatabaseManagement(
                managerCredentials.username,
                managerCredentials.password
            );
            setManagerCredentials((current) => ({ ...current, password: "" }));
            setManagerAuthenticated(true);
        } catch (loginError) {
            setManagerLoginError(loginError.message);
        } finally {
            setManagerLoginBusy(false);
        }
    }

    async function handleManagerLogout() {
        try {
            await logoutDatabaseManagement();
        } catch {
            // Lock the interface locally even if the logout request fails.
        }
        setManagerAuthenticated(false);
        setRecords([]);
        setSelected([]);
        setSummary({ total: 0, departments: [] });
        setEditing(null);
    }

    function requestSecondSecurity(title, operation) {
        pendingSecurityAction.current = operation;
        setSecurityTitle(title);
        setSecurityPassword("");
        setSecurityError("");
    }

    async function handleSecondSecuritySubmit(event) {
        event.preventDefault();
        if (!securityPassword || !pendingSecurityAction.current) return;

        setSecurityBusy(true);
        setSecurityError("");
        try {
            await pendingSecurityAction.current(securityPassword);
            pendingSecurityAction.current = null;
            setSecurityTitle("");
            setSecurityPassword("");
        } catch (actionError) {
            const message = actionError.message || "Authorization failed.";
            setSecurityError(message);
            if (message.includes("Separate Database Management login required.")) {
                pendingSecurityAction.current = null;
                setSecurityTitle("");
                setManagerAuthenticated(false);
            }
        } finally {
            setSecurityBusy(false);
        }
    }

    function closeSecondSecurity() {
        if (securityBusy) return;
        pendingSecurityAction.current = null;
        setSecurityTitle("");
        setSecurityPassword("");
        setSecurityError("");
    }

    function changeFilter(key, value) {
        setFilters((current) => ({ ...current, [key]: value }));
    }

    async function handleApplyFilters(event) {
        event.preventDefault();
        await loadData(filters);
    }

    function toggleOne(id) {
        setSelected((current) => current.includes(id)
            ? current.filter((item) => item !== id)
            : [...current, id]
        );
    }

    const allVisibleSelected = records.length > 0 && records.every(
        (record) => selected.includes(record.grievance_id)
    );

    function toggleVisible() {
        setSelected(allVisibleSelected
            ? []
            : records.map((record) => record.grievance_id)
        );
    }

    function openEdit(record) {
        setEditing(record.grievance_id);
        setEditForm({
            citizen_name: record.citizen_name || "",
            summary: record.summary || "",
            description: record.description || "",
            department_reason: record.department_reason || "",
            status: record.status || "REGISTERED",
        });
        setError("");
        setNotice("");
    }

    function handleSaveEdit(event) {
        event.preventDefault();
        requestSecondSecurity(text.editTitle, async (securityPasswordValue) => {
            setError("");
            setNotice("");
            await updateManagementGrievance(editing, editForm, securityPasswordValue);
            setEditing(null);
            setNotice(text.saved);
            await loadData(filters);
        });
    }

    function handleDeleteSelected() {
        if (!selected.length) return;
        const prompt = isMalayalam
            ? `${selected.length} പരാതികൾ സ്ഥിരമായി മായ്ക്കണോ?`
            : `Permanently delete ${selected.length} selected grievance(s) and their uploaded documents?`;
        if (!window.confirm(prompt)) return;

        requestSecondSecurity(text.selectedDelete, async (securityPasswordValue) => {
            setError("");
            setNotice("");
            const result = await deleteSelectedGrievances(selected, securityPasswordValue);
            setNotice(`${text.deleted} ${result.deleted_count} record(s).`);
            await loadData(filters);
        });
    }

    const canDeleteFiltered = Boolean(
        filters.department_code || filters.status || filters.date_from || filters.date_to
    );

    function handleDeleteFiltered() {
        if (!canDeleteFiltered) return;
        const prompt = isMalayalam
            ? "നിലവിലെ വകുപ്പ്/നില/തീയതി ഫിൽട്ടറുമായി പൊരുത്തപ്പെടുന്ന എല്ലാ പരാതികളും മായ്ക്കണോ?"
            : `Permanently delete every grievance matching the active department/status/date filters? The current view shows ${records.length} record(s).`;
        if (!window.confirm(prompt)) return;

        requestSecondSecurity(text.filteredDelete, async (securityPasswordValue) => {
            setError("");
            setNotice("");
            const result = await deleteFilteredGrievances({
                department_code: filters.department_code || null,
                status: filters.status || null,
                date_from: filters.date_from || null,
                date_to: filters.date_to || null,
            }, securityPasswordValue);
            setNotice(`${text.deleted} ${result.deleted_count} record(s).`);
            await loadData(filters);
        });
    }

    function handleClearAll() {
        if (clearPhrase !== "DELETE ALL GRIEVANCES") return;

        requestSecondSecurity(text.clearAll, async (securityPasswordValue) => {
            setError("");
            setNotice("");
            const result = await clearAllGrievances(clearPhrase, securityPasswordValue);
            setShowClear(false);
            setClearPhrase("");
            setFilters(EMPTY_FILTERS);
            setNotice(`${text.cleared} ${result.deleted_count} record(s).`);
            await loadData(EMPTY_FILTERS);
        });
    }

    if (managerAuthChecking) {
        return (
            <section className="flex min-h-[60vh] items-center justify-center bg-slate-50 p-6">
                <p className="text-sm text-gray-600">{text.authChecking}</p>
            </section>
        );
    }

    if (!managerAuthenticated) {
        return (
            <section className="flex min-h-[60vh] items-center justify-center bg-slate-50 px-4 py-8">
                <form onSubmit={handleManagerLogin} className="w-full max-w-md space-y-4 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                    <div className="text-center">
                        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-700">
                            <span className="text-xl" aria-hidden="true">🔒</span>
                        </div>
                        <h2 className="text-xl font-bold text-gray-800">{text.loginTitle}</h2>
                        <p className="mt-2 text-sm text-gray-500">{text.loginDescription}</p>
                    </div>
                    <label className="block text-sm font-medium text-gray-700">
                        {text.username}
                        <input autoComplete="username" required value={managerCredentials.username}
                            onChange={(event) => setManagerCredentials({ ...managerCredentials, username: event.target.value })}
                            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                    </label>
                    <label className="block text-sm font-medium text-gray-700">
                        {text.password}
                        <input type="password" autoComplete="current-password" required value={managerCredentials.password}
                            onChange={(event) => setManagerCredentials({ ...managerCredentials, password: event.target.value })}
                            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                    </label>
                    {managerLoginError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{managerLoginError}</p>}
                    <button type="submit" disabled={managerLoginBusy || !managerCredentials.username || !managerCredentials.password}
                        className="w-full rounded-lg bg-gray-800 px-4 py-2.5 text-sm font-semibold text-white hover:bg-gray-900 disabled:opacity-50">
                        {managerLoginBusy ? text.loading : text.login}
                    </button>
                </form>
            </section>
        );
    }

    return (
        <section className="min-h-full bg-slate-50 px-4 py-6 sm:px-8">
            <div className="mx-auto max-w-7xl space-y-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-800">{text.title}</h2>
                        <p className="mt-1 text-sm text-gray-500">{text.subtitle}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <button type="button" onClick={handleManagerLogout} disabled={busy || securityBusy}
                            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
                            {text.logoutManager}
                        </button>
                        <button type="button" onClick={() => loadData(filters)} disabled={loading || busy}
                            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
                            {text.refresh}
                        </button>
                        <button type="button" onClick={handleDeleteSelected} disabled={!selected.length || busy}
                            className="rounded-lg border border-red-300 bg-white px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40">
                            {text.selectedDelete} ({selected.length})
                        </button>
                        <button type="button" onClick={handleDeleteFiltered} disabled={!canDeleteFiltered || busy}
                            title={!canDeleteFiltered ? text.chooseFilter : ""}
                            className="rounded-lg border border-orange-300 bg-white px-3 py-2 text-sm font-medium text-orange-700 hover:bg-orange-50 disabled:cursor-not-allowed disabled:opacity-40">
                            {text.filteredDelete}
                        </button>
                        <button type="button" onClick={() => setShowClear(true)} disabled={busy || loading}
                            className="rounded-lg bg-red-700 px-3 py-2 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-50">
                            {text.clearAll}
                        </button>
                    </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                        <p className="text-xs text-gray-500">{text.total}</p>
                        <p className="mt-1 text-3xl font-bold text-gray-800">{summary.total ?? 0}</p>
                    </div>
                    {(summary.departments || []).filter((item) => item.total > 0).slice(0, 3).map((item) => (
                        <div key={item.department_code} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                            <p className="text-xs text-gray-500">{item.department_code}</p>
                            <p className="mt-1 text-3xl font-bold text-gray-800">{item.total}</p>
                        </div>
                    ))}
                </div>

                <form onSubmit={handleApplyFilters} className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm md:grid-cols-6">
                    <input value={filters.search} onChange={(event) => changeFilter("search", event.target.value)}
                        placeholder={text.search} className="rounded-lg border border-gray-300 px-3 py-2 text-sm md:col-span-2" />
                    <select value={filters.department_code} onChange={(event) => changeFilter("department_code", event.target.value)}
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
                        <option value="">{text.allDepartments}</option>
                        {DEPARTMENTS.map((department) => <option key={department} value={department}>{department}</option>)}
                    </select>
                    <select value={filters.status} onChange={(event) => changeFilter("status", event.target.value)}
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm">
                        <option value="">{text.allStatuses}</option>
                        {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
                    </select>
                    <input type="date" aria-label={text.from} value={filters.date_from} onChange={(event) => changeFilter("date_from", event.target.value)}
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm" />
                    <div className="flex gap-2">
                        <input type="date" aria-label={text.to} value={filters.date_to} onChange={(event) => changeFilter("date_to", event.target.value)}
                            className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm" />
                        <button type="submit" disabled={loading || busy}
                            className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
                            {text.apply}
                        </button>
                    </div>
                </form>

                {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
                {notice && <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">{notice}</div>}

                <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                    <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
                        <p className="text-sm font-semibold text-gray-700">{text.count}: {records.length}</p>
                        <label className="flex items-center gap-2 text-sm text-gray-600">
                            <input type="checkbox" checked={allVisibleSelected} onChange={toggleVisible} disabled={!records.length} />
                            {text.select}
                        </label>
                    </div>
                    {loading ? (
                        <p className="p-8 text-center text-sm text-gray-500">{text.loading}</p>
                    ) : records.length === 0 ? (
                        <p className="p-8 text-center text-sm text-gray-500">{text.noRecords}</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full min-w-[1050px] text-left text-sm">
                                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                                    <tr>
                                        <th className="w-10 p-3"></th>
                                        <th className="p-3">{text.id}</th>
                                        <th className="p-3">{text.name}</th>
                                        <th className="p-3">{text.department}</th>
                                        <th className="p-3">{text.slot}</th>
                                        <th className="p-3">{text.status}</th>
                                        <th className="p-3">{text.registered}</th>
                                        <th className="p-3">{text.actions}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {records.map((record) => (
                                        <tr key={record.grievance_id} className="border-t border-gray-100 hover:bg-gray-50">
                                            <td className="p-3"><input type="checkbox" checked={selected.includes(record.grievance_id)} onChange={() => toggleOne(record.grievance_id)} /></td>
                                            <td className="p-3 font-semibold text-blue-700">{record.grievance_id}</td>
                                            <td className="p-3">{record.citizen_name || (isMalayalam ? "പേര് ലഭ്യമല്ല" : "Not available")}</td>
                                            <td className="p-3">{record.department_code}</td>
                                            <td className="p-3">{record.department_slot}</td>
                                            <td className="p-3">{record.status}</td>
                                            <td className="p-3 whitespace-nowrap">{record.registered_at}</td>
                                            <td className="p-3"><button type="button" onClick={() => openEdit(record)} className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100">{text.edit}</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {showClear && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                        <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
                            <h3 className="text-lg font-bold text-red-700">{text.clearAll}</h3>
                            <p className="mt-3 text-sm text-gray-700">{text.clearWarning}</p>
                            <p className="mt-4 text-sm font-semibold text-gray-800">{text.confirmClear}</p>
                            <input value={clearPhrase} onChange={(event) => setClearPhrase(event.target.value)}
                                className="mt-2 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                                placeholder="DELETE ALL GRIEVANCES" />
                            <div className="mt-5 flex flex-wrap justify-end gap-2">
                                <button type="button" onClick={() => { setShowClear(false); setClearPhrase(""); }} disabled={busy}
                                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm">{text.cancel}</button>
                                <button type="button" onClick={handleClearAll} disabled={busy || clearPhrase !== "DELETE ALL GRIEVANCES"}
                                    className="rounded-lg bg-red-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">
                                    {busy ? text.loading : text.confirm}
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {editing && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/50 p-4">
                        <form onSubmit={handleSaveEdit} className="my-8 w-full max-w-3xl space-y-4 rounded-xl bg-white p-6 shadow-xl">
                            <div className="flex items-center justify-between gap-3">
                                <h3 className="text-lg font-bold text-gray-800">{text.editTitle}: {editing}</h3>
                                <button type="button" onClick={() => setEditing(null)} className="text-sm text-gray-500">{text.close}</button>
                            </div>
                            <p className="text-xs text-gray-500">{text.immutable}</p>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.name}
                                <input value={editForm.citizen_name} onChange={(event) => setEditForm({ ...editForm, citizen_name: event.target.value })}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.summary}
                                <textarea required rows={3} value={editForm.summary} onChange={(event) => setEditForm({ ...editForm, summary: event.target.value })}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.description}
                                <textarea required rows={7} value={editForm.description} onChange={(event) => setEditForm({ ...editForm, description: event.target.value })}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.reason}
                                <textarea rows={2} value={editForm.department_reason} onChange={(event) => setEditForm({ ...editForm, department_reason: event.target.value })}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.status}
                                <select value={editForm.status} onChange={(event) => setEditForm({ ...editForm, status: event.target.value })}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2">
                                    {STATUSES.map((status) => <option key={status} value={status}>{status}</option>)}
                                </select>
                            </label>
                            <div className="flex justify-end gap-2">
                                <button type="button" onClick={() => setEditing(null)} disabled={busy}
                                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm">{text.cancel}</button>
                                <button type="submit" disabled={busy}
                                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
                                    {busy ? text.loading : text.save}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {securityTitle && (
                    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 p-4">
                        <form onSubmit={handleSecondSecuritySubmit} className="w-full max-w-md space-y-4 rounded-xl bg-white p-6 shadow-2xl">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{text.secondAuthTitle}</h3>
                                <p className="mt-1 text-sm text-gray-600">{text.secondAuthDescription}</p>
                                <p className="mt-2 text-sm font-semibold text-gray-800">{securityTitle}</p>
                            </div>
                            <label className="block text-sm font-medium text-gray-700">
                                {text.actionPassword}
                                <input type="password" autoComplete="current-password" autoFocus required value={securityPassword}
                                    onChange={(event) => setSecurityPassword(event.target.value)}
                                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
                            </label>
                            {securityError && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{securityError}</p>}
                            <div className="flex justify-end gap-2">
                                <button type="button" onClick={closeSecondSecurity} disabled={securityBusy}
                                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700">{text.cancel}</button>
                                <button type="submit" disabled={securityBusy || !securityPassword}
                                    className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
                                    {securityBusy ? text.loading : text.confirmAction}
                                </button>
                            </div>
                        </form>
                    </div>
                )}
            </div>
        </section>
    );
}
