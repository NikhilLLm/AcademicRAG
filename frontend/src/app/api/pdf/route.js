import { NextResponse } from "next/server";
export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const pdfUrl = searchParams.get("url");

  if (!pdfUrl) {
    return NextResponse.json(
      { error: "Missing pdf url" },
      { status: 400 }
    );
  }

  try {
    const res = await fetch(pdfUrl);

    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to fetch PDF" },
        { status: 500 }
      );
    }

    const blob = await res.arrayBuffer();

    return new NextResponse(blob, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": "inline",
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: "PDF fetch failed" },
      { status: 500 }
    );
  }
}
