import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://20.127.80.79:8000";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const res = await fetch(`${API_URL}/api/compare`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message }, { status: 502 });
  }
}
