// . /api/notes/status/[jobId]/

export async function GET(req, { params }) {
  const { jobId } = await params;

  const res = await fetch(`http://localhost:8000/job-status/${jobId}`);

  if (!res.ok) {
    return Response.json(
      { error: "Failed to fetch job status" },
      { status: 500 }
    );
  }

  return Response.json(await res.json());
}
