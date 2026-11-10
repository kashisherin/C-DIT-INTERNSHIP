
import { useState } from "react";

// Chat input box and Send button.
export default function ChatInput({ onSend, disabled, language = "en" }) {
    const [text, setText] = useState("");
    const isMalayalam = language === "ml";

    function handleSubmit(event) {
        event.preventDefault();

        const question = text.trim();

        if (!question || disabled) return;

        onSend(question);
        setText("");
    }

    return (
        <form
            onSubmit={handleSubmit}
            className="flex gap-2 border-t border-gray-200 bg-white p-4"
        >
            <input
                type="text"
                value={text}
                onChange={(event) => setText(event.target.value)}
                placeholder={
                    isMalayalam
                        ? "കേരളത്തെക്കുറിച്ച് ഒരു ചോദ്യം ചോദിക്കൂ..."
                        : "Ask a question about Kerala..."
                }
                className="min-w-0 flex-1 rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

            <button
                type="submit"
                disabled={disabled || !text.trim()}
                className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
                {isMalayalam ? "അയയ്ക്കുക" : "Send"}
            </button>
        </form>
    );
}
