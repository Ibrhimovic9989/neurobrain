import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://20.127.80.79:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/connectivity`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ detail: e.message }, { status: 502 });
  }
}
