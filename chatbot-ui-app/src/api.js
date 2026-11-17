
const API_URL =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ============================================================
// COMMON API REQUEST HANDLER
// ============================================================

async function request(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API_URL}${path}`, {
            ...options,
            credentials: "include",
        });
    } catch {
        throw new Error(
            "Cannot reach the API. Is the backend running?"
        );
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new Error(`Invalid server response (${response.status})`);
    }

    if (!response.ok) {
        throw new Error(
            data.detail || `Request failed (${response.status})`
        );
    }

    return data;
}

function postJson(path, body) {
    return request(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

// ============================================================
// CITIZEN PORTAL
// ============================================================

export function askQuestion(question, language = "en") {
    return postJson("/ask", {
        question,
        response_language: language,
    });
}

export function processGrievance(file, language = "en") {
    const form = new FormData();
    form.append("file", file);
    form.append("language", language);

    return request("/grievance/process", {
        method: "POST",
        body: form,
    });
}

export function getDepartments() {
    return request("/departments");
}

// ============================================================
// OFFICIAL AUTHENTICATION
// ============================================================

export function loginOfficial(username, password) {
    return postJson("/official/login", {
        username,
        password,
    });
}

export function getOfficialSession() {
    return request("/official/session");
}

export function logoutOfficial() {
    return request("/official/logout", {
        method: "POST",
    });
}

// ============================================================
// OFFICIAL PORTAL AI ASSISTANT
// ============================================================

export function askOfficialQuestion(question, history = []) {
    return postJson("/official/chat", {
        question,
        history,
    });
}

// ============================================================
// OFFICIAL GRIEVANCE STATUS UPDATE
// ============================================================

export function updateGrievanceStatus(grievanceId, status, securityPassword) {
    return request(
        `/official/grievances/id/${encodeURIComponent(grievanceId)}/status`,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ status, security_password: securityPassword }),
        }
    );
}

// ============================================================
// SEPARATE DATABASE MANAGEMENT AUTHENTICATION
// ============================================================

export function loginDatabaseManagement(username, password) {
    return postJson("/official/database/access/login", {
        username,
        password,
    });
}

export function getDatabaseManagementSession() {
    return request("/official/database/access/session");
}

export function logoutDatabaseManagement() {
    return request("/official/database/access/logout", {
        method: "POST",
    });
}

// ============================================================
// OFFICIAL DATABASE MANAGEMENT
// ============================================================

export function getManagementGrievances(filters = {}) {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && String(value).trim() !== "") {
            params.set(key, String(value));
        }
    });

    const query = params.toString();
    return request(`/official/database/grievances${query ? `?${query}` : ""}`);
}

export function getManagementSummary() {
    return request("/official/database/summary");
}

export function updateManagementGrievance(grievanceId, payload, securityPassword) {
    return request(
        `/official/database/grievances/${encodeURIComponent(grievanceId)}`,
        {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...payload, security_password: securityPassword }),
        }
    );
}

export function deleteSelectedGrievances(grievanceIds, securityPassword) {
    return postJson("/official/database/grievances/delete-selected", {
        grievance_ids: grievanceIds,
        security_password: securityPassword,
    });
}

export function deleteFilteredGrievances(filters, securityPassword) {
    return postJson("/official/database/grievances/delete-filtered", {
        ...filters,
        security_password: securityPassword,
    });
}

export function clearAllGrievances(confirmation, securityPassword) {
    return postJson("/official/database/clear-all", {
        confirmation,
        security_password: securityPassword,
    });
}
