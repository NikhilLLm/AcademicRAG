export async function POST(req, { params }) {
  const { chatSessionId } = await params;
  const body = await req.json();

  const response = await fetch(
    `http://localhost:8000/chat/${chatSessionId}/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message: body.message }),
    }
  );

  if (!response.ok) {
    const errText = await response.text();
    return new Response(errText, { status: 500 });
  }

  const text = await response.text(); // 👈 IMPORTANT
  return new Response(text, {
    headers: { "Content-Type": "text/plain" },
  });
}
