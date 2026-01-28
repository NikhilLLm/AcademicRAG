//   . /api/notes/start/[id]/
// Updated: Now uses JSON instead of FormData
export async function POST(req, { params }) {
  const { id } = await params;

  const response = await fetch("http://localhost:8000/start_short_notes", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ vector_index: id }),
  });

  if (!response.ok) {
    return Response.json(
      { error: "Backend failed to start job" },
      { status: 500 }
    );
  }

  const data = await response.json();
  return Response.json(data); // { job_id }
}
