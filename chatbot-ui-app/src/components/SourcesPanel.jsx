import { useEffect, useState } from "react";
import { fetchPage, getSources } from "../api";

// Side panel: shows the web pages in the database and lets you add a new one
export default function SourcesPanel() {
    const [sources, setSources] = useState([]);
    const [url, setUrl] = useState("");
    const [busy, setBusy] = useState(false);
    const [status, setStatus] = useState("");

    async function loadSources() {
        try {
            setSources(await getSources());
        } catch (error) {
            setStatus(error.message);
        }
    }

    // Load the list once when the panel first appears
    useEffect(() => {
        getSources()
            .then(setSources)
            .catch((error) => setStatus(error.message));
    }, []);

    async function handleAdd(event) {
        event.preventDefault();

        if (!url.trim()) return;

        setBusy(true);
        setStatus("Fetching and indexing... this can take a minute.");

        try {
            const page = await fetchPage(url.trim());

            setStatus(
                `Added "${page.title}" (${page.chunks_indexed} chunks).`
            );

            setUrl("");
            await loadSources();
        } catch (error) {
            setStatus(error.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="flex flex-col gap-4">
            <div>
                <h2 className="text-lg font-semibold">Knowledge sources</h2>
                <p className="text-sm text-gray-500">
                    Web pages the bot can answer from
                </p>
            </div>

            <ul className="space-y-3">
                {sources.length === 0 && (
                    <li className="text-sm text-gray-500">
                        No pages yet. Add one below.
                    </li>
                )}

                {sources.map((s) => (
                    <li
                        key={s.source}
                        className="flex flex-col gap-1 border-b border-gray-200 pb-3"
                    >
                        <span className="break-all text-sm font-medium">
                            {s.source}
                        </span>

                        <span className="text-xs text-gray-500">
                            {s.chunks} chunks
                        </span>
                    </li>
                ))}
            </ul>

            <form onSubmit={handleAdd} className="flex flex-col gap-3">
                <input
                    type="url"
                    value={url}
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://en.wikipedia.org/wiki/..."
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                    outline-none focus:border-blue-500"
                />

                <button
                    type="submit"
                    disabled={busy || !url.trim()}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium
                    text-white hover:bg-blue-700 disabled:cursor-not-allowed
                    disabled:bg-gray-300"
                >
                    {busy ? "Adding..." : "Add web page"}
                </button>
            </form>

            {status && (
                <p className="text-sm text-gray-600">
                    {status}
                </p>
            )}
        </div>
    );
}