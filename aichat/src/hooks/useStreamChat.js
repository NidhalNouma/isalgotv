export function useStreamChat(sessionId, userMessage, onChunk, onComplete) {
  const stream = () => {
    const source = new EventSource(
      `/chat/stream/?session_id=${sessionId}&message=${encodeURIComponent(
        userMessage
      )}`
    );

    let fullReply = "";

    source.onmessage = (event) => {
      const text = event.data;
      onChunk(text);
      fullReply += text;
    };

    source.onerror = () => {
      source.close();
      onComplete(fullReply);
    };
  };

  return { stream };
}
