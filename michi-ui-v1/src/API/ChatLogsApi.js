
export async function fetchChatLogs() {
  const response = await fetch('http://18.141.160.29/api/chat-logs');
  if (!response.ok) {
    throw new Error('Failed to fetch chat logs');
  }
  return await response.json();
}