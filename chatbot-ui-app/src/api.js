// The address of our FastAPI server
const API_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API_URL}${path}`, options);
    } catch {
        throw new Error(
            "Cannot reach the API. Is uvicorn running on port 8000?"
        );
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || `Request failed (${response.status})`);
    }

    return data;
}

// Send JSON (used by the chatbot)
function postJson(path, body) {
    return request(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
}

export function askQuestion(question) {
    return postJson("/ask", { question });
}

// Send a file. FormData sets the right Content-Type (multipart) by itself.
export function processGrievance(file) {
    const form = new FormData();
    form.append("file", file);

    return request("/grievance/process", {
        method: "POST",
        body: form,
    });
}

export function getDepartments() {
    return request("/departments");
}