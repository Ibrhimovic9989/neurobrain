import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "https://neurobrain-api.eastus.cloudapp.azure.com";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const res = await fetch(`${API_URL}/api/calibrate/fit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ detail: msg }, { status: 502 });
  }
}
