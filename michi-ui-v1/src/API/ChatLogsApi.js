const SERVER_ORIGIN = import.meta.env.VITE_API_BASE_URL; // Flask base URL

export async function fetchChatLogs(robotId) {
  const url = robotId
    ? `https://${SERVER_ORIGIN}/api/chat-logs?robot_id=${encodeURIComponent(robotId)}`
    : `https://${SERVER_ORIGIN}/api/chat-logs`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch chat logs');
  }
  return await response.json();
}