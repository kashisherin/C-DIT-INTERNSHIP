
// One chat bubble. role is "user", "bot" or "error".
export default function ChatMessage({ role, text, sources = [] }) {
    const isUser = role === "user";

    const bubbleStyle = {
        user: "bg-blue-600 text-white rounded-br-sm",
        bot: "bg-white text-gray-800 border border-gray-200 rounded-bl-sm",
        error: "bg-red-50 text-red-700 border border-red-200 rounded-bl-sm",
    }[role];

    // Keep each source page once and retain its lowest distance
    const sourceMap = new Map();

    sources.forEach((source) => {
        const existing = sourceMap.get(source.source);

        if (
            !existing ||
            (typeof source.distance === "number" &&
                (typeof existing.distance !== "number" ||
                    source.distance < existing.distance))
        ) {
            sourceMap.set(source.source, source);
        }
    });

    const links = [...sourceMap.values()];

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

                    <ul className="list-disc pl-5 space-y-1">
                        {links.map((source) => (
                            <li key={source.source}>
                                {source.source.startsWith("http") ? (
                                    <a
                                        href={source.source}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-blue-600 hover:underline"
                                    >
                                        {source.source}
                                    </a>
                                ) : (
                                    <span className="text-gray-600">
                                        {source.source}
                                    </span>
                                )}

                                {typeof source.distance === "number" && (
                                    <span className="ml-2 text-gray-500">
                                        (Distance: {source.distance.toFixed(3)})
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
