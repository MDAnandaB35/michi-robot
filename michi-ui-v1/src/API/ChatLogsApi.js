
export async function fetchChatLogs() {
  const response = await fetch('http://localhost:5000/api/chat-logs');
  if (!response.ok) {
    throw new Error('Failed to fetch chat logs');
  }
  return await response.json();
}