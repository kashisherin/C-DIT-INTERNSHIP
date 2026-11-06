import { useState } from "react";
import { processGrievance } from "../api";

const ACCEPTED = ".jpg,.jpeg,.png,.webp,.pdf";

const isPdf = (file) => file.name.toLowerCase().endsWith(".pdf");

// Pick or drop a file, preview it, and send it to the AI.
// The parent page decides what to do with the result (onResult).
export default function GrievanceUpload({ onResult, onClear }) {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");

    function selectFile(chosen) {
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }

        // Free the old preview
        setFile(chosen || null);

        setPreviewUrl(
            chosen && !isPdf(chosen)
                ? URL.createObjectURL(chosen)
                : null
        );

        setError("");
        onClear(); // Old result no longer matches
    }

    function handleDrop(event) {
        event.preventDefault();
        selectFile(event.dataTransfer.files[0]);
    }

    async function handleProcess() {
        if (!file || busy) return;

        setBusy(true);
        setError("");

        try {
            onResult(await processGrievance(file));
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="space-y-4">
            <div>
                <h2 className="text-xl font-semibold text-gray-800">
                    Grievance letter
                </h2>

                <p className="text-sm text-gray-500">
                    Photo or scan, handwritten or typed
                </p>
            </div>

            {/* File upload area */}
            <label
                onDragOver={(event) => event.preventDefault()}
                onDrop={handleDrop}
                className="flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-4 text-center hover:border-blue-400"
            >
                <input
                    type="file"
                    accept={ACCEPTED}
                    className="hidden"
                    onChange={(event) =>
                        selectFile(event.target.files[0])
                    }
                />

                {/* Image preview */}
                {previewUrl && (
                    <img
                        src={previewUrl}
                        alt="Grievance preview"
                        className="mb-3 max-h-48 max-w-full rounded-lg object-contain"
                    />
                )}

                {/* PDF preview information */}
                {file && !previewUrl && (
                    <p className="mb-3 text-sm text-gray-700">
                        PDF: {file.name}
                    </p>
                )}

                {/* Default upload instructions */}
                {!file && (
                    <>
                        <p className="font-medium text-gray-700">
                            Click to choose a file, or drop it here
                        </p>

                        <p className="mt-2 text-xs text-gray-500">
                            JPG, PNG, WEBP or PDF, up to 10 MB
                        </p>
                    </>
                )}
            </label>

            {/* Selected file name */}
            {file && (
                <p className="text-sm text-gray-600">
                    {file.name}
                </p>
            )}

            {/* Process button */}
            <button
                type="button"
                onClick={handleProcess}
                disabled={!file || busy}
                className="w-full rounded-xl bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
                {busy ? "Reading the letter..." : "Process with AI"}
            </button>

            {/* Processing information */}
            {busy && (
                <p className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
                    The AI is reading the handwriting. This can take 1-3
                    minutes on a laptop.
                </p>
            )}

            {/* Error message */}
            {error && (
                <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </p>
            )}
        </div>
    );
}