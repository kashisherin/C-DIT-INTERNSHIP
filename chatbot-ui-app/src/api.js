// The address of our FastAPI server
const API_URL = "/api";

async function request(path, options = {}) {
    let response;

    try {
        response = await fetch(`${API_URL}${path}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });
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

export function askQuestion(question) {
    return request("/ask", {
        method: "POST",
        body: JSON.stringify({ question }),
    });
}

export function fetchPage(url) {
    return request("/fetch", {
        method: "POST",
        body: JSON.stringify({ url }),
    });
}

export function getSources() {
    return request("/sources");
}