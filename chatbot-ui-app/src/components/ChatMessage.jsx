// One chat bubble. role is "user", "bot" or "error".
export default function ChatMessage({ role, text, sources = [] }) {
    const isUser = role === "user";

    const bubbleStyle = {
        user: "bg-blue-600 text-white rounded-br-sm",
        bot: "bg-white text-gray-800 border border-gray-200 rounded-bl-sm",
        error: "bg-red-50 text-red-700 border border-red-200 rounded-bl-sm",
    }[role];

    // The same web page can appear in several chunks; show each page once
    const links = [...new Set(sources.map((s) => s.source))];

    return (
        <div>
            <div
                className={`rounded-2xl p-4 ${bubbleStyle} ${
                    isUser ? "ml-auto" : "mr-auto"
                }`}
            >
                {text}
            </div>

            {links.length > 0 && (
                <div className="mt-2 text-sm">
                    <p className="font-semibold">Sources</p>

                    <ul className="list-disc pl-5">
                        {links.map((link) => (
                            <li key={link}>
                                {link.startsWith("http") ? (
                                    <a
                                        href={link}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        {link}
                                    </a>
                                ) : (
                                    <span className="text-gray-600">
                                        {link}
                                    </span>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

// Three bouncing dots while we wait for the answer
export function TypingIndicator() {
    return (
        <div className="flex justify-start">
            <div
                className="flex gap-1 rounded-2xl rounded-bl-sm border border-gray-200
                bg-white px-4 py-4 shadow-sm"
            >
                {[0, 150, 300].map((delay) => (
                    <span
                        key={delay}
                        className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
                        style={{ animationDelay: `${delay}ms` }}
                    />
                ))}
            </div>
        </div>
    );
}