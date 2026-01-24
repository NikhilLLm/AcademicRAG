export async function GET(req, { params }) {
  const { chatSessionId } = await params; // ✅ correct
  console.log("API route received chatId:", chatSessionId);

  try {
    const res = await fetch(`http://localhost:8000/chat-job-status/${chatSessionId}`);
    const data = await res.json();
    console.log("Backend response:", data);
    return new Response(JSON.stringify(data), { status: 200 });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), { status: 500 });
  }
}
