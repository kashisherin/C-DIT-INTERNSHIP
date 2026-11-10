
import { useEffect, useRef, useState } from "react";
import { askQuestion } from "../api";
import { useLanguage } from "../context/LanguageContext";
import ChatMessage, { TypingIndicator } from "./ChatMessage";
import ChatInput from "./ChatInput";

export default function ChatWidget() {
    const { language } = useLanguage();
    const isMalayalam = language === "ml";

    const welcomeMessage = isMalayalam
        ? "നമസ്കാരം! കേരളത്തെയും സർക്കാർ സേവനങ്ങളെയും കുറിച്ച് എന്തും ചോദിക്കാം."
        : "Hi! Ask me anything about Kerala and its government services.";

    const [open, setOpen] = useState(false);
    const [messages, setMessages] = useState([
        { role: "bot", text: welcomeMessage },
    ]);
    const [loading, setLoading] = useState(false);

    const bottomRef = useRef(null);

    // Update the welcome message when the language changes,
    // provided the user has not started a conversation.
    useEffect(() => {
        setMessages((prev) => {
            if (prev.length === 1 && prev[0].role === "bot") {
                return [{ role: "bot", text: welcomeMessage }];
            }
            return prev;
        });
    }, [welcomeMessage]);

    // Scroll to the newest message.
    useEffect(() => {
        if (open) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, loading, open]);

    async function handleSend(question) {
        setMessages((prev) => [
            ...prev,
            { role: "user", text: question },
        ]);

        setLoading(true);

        try {
            const data = await askQuestion(question, language);

            setMessages((prev) => [
                ...prev,
                {
                    role: "bot",
                    text: data.answer,
                    sources: data.sources,
                },
            ]);
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "error",
                    text: error.message,
                },
            ]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <>
            {open && (
                <div className="fixed bottom-24 right-6 z-50 flex h-[500px] w-[350px] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl">

                    {/* Chat header */}
                    <div className="flex items-center justify-between bg-blue-600 px-4 py-3 text-white">
                        <div>
                            <h2 className="font-semibold">
                                {isMalayalam
                                    ? "കേരള അസിസ്റ്റന്റ്"
                                    : "Kerala Assistant"}
                            </h2>

                            <p className="text-xs text-blue-100">
                                {isMalayalam
                                    ? "ഔദ്യോഗിക വെബ് പേജുകളിൽ നിന്നുള്ള ഉത്തരങ്ങൾ"
                                    : "Answers from official web pages"}
                            </p>
                        </div>

                        <button
                            onClick={() => setOpen(false)}
                            aria-label={isMalayalam ? "ചാറ്റ് അടയ്ക്കുക" : "Close chat"}
                            className="rounded-full p-1 hover:bg-blue-500"
                        >
                            <CloseIcon />
                        </button>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 space-y-4 overflow-y-auto bg-gray-50 p-4">
                        {messages.map((message, index) => (
                            <ChatMessage
                                key={index}
                                role={message.role}
                                text={message.text}
                                sources={message.sources || []}
                                language={language}
                            />
                        ))}

                        {loading && <TypingIndicator />}

                        <div ref={bottomRef} />
                    </div>

                    {/* Chat input */}
                    <ChatInput
                        onSend={handleSend}
                        disabled={loading}
                        language={language}
                    />
                </div>
            )}

            {/* Floating chat button */}
            <button
                onClick={() => setOpen(!open)}
                aria-label={
                    open
                        ? (isMalayalam ? "ചാറ്റ് അടയ്ക്കുക" : "Close chat")
                        : (isMalayalam ? "ചാറ്റ് തുറക്കുക" : "Open chat")
                }
                className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg hover:bg-blue-700"
            >
                {open ? <CloseIcon /> : <ChatIcon />}
            </button>
        </>
    );
}

function ChatIcon() {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
    );
}

function CloseIcon() {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
        </svg>
    );
}
