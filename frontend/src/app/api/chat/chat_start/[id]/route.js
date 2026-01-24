export async function POST(req, { params }) {
  const { id } = await params; // no await needed

  const formData = new FormData();
  formData.append("vector_index", id);

  const response = await fetch("http://localhost:8000/init_chat", {
    method: "POST",
    body: formData,
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
