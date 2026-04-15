import { NextResponse } from "next/server";

const API_URL = process.env.API_URL || "https://neurobrain-api.eastus.cloudapp.azure.com";

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/calibrate/stimuli`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ detail: msg }, { status: 502 });
  }
}
