import { useState } from "react";

// The text box and Send button at the bottom of the chat
export default function ChatInput({ onSend, disabled }) {
    const [text, setText] = useState("");

    function handleSubmit(event) {
        event.preventDefault(); // stop the page from reloading

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
                placeholder="Ask a question about Kerala..."
                className="flex-1 rounded-xl border border-gray-300 px-4 py-3 outline-none
                focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

            <button
                type="submit"
                disabled={disabled || !text.trim()}
                className="rounded-xl bg-blue-600 px-5 py-3 font-medium text-white
                hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
            >
                Send
            </button>
        </form>
    );
}