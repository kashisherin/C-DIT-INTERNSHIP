
const API_URL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API_URL}${path}`, options);
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

// RAG-based question answering
export function askQuestion(question, language = "en") {
    return postJson("/ask", {
        question,
        response_language: language,
    });
}

// Grievance document processing using Gemma 4
export function processGrievance(file, language = "en") {
    const form = new FormData();
    form.append("file", file);
    form.append("language", language);

    return request("/grievance/process", {
        method: "POST",
        body: form,
    });
}

// Retrieve available government departments
export function getDepartments() {
    return request("/departments");
}
