const SERVER_ORIGIN = import.meta.env.VITE_API_BASE_URL; // Flask base URL

export async function fetchChatLogs() {
  const response = await fetch(`http://${SERVER_ORIGIN}/api/chat-logs`);
  if (!response.ok) {
    throw new Error('Failed to fetch chat logs');
  }
  return await response.json();
}