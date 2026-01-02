//   . /api/notes/start/[id]/
export async function POST(req, { params }) {
  const { id } = await params;

  const formData = new FormData();
  formData.append("vector_index", id);

  const response = await fetch("http://localhost:8000/start_short_notes", {
    method: "POST",
    body: formData,
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
