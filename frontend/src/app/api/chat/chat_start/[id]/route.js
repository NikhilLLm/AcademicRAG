// Updated: Now uses JSON instead of FormData
export async function POST(req, { params }) {
  const { id } = await params; // no await needed

  const response = await fetch("http://localhost:8000/init_chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ vector_index: id }),
  });

  if (!response.ok) {
    return Response.json(
      { error: "Backend failed to start chat job" },
      { status: 500 }
    );
  }

  const data = await response.json();
  return Response.json(data); // { chat_session_id }
}
