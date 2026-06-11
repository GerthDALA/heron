import { NextRequest, NextResponse } from "next/server";

// Thin proxy to the FastAPI backend — lets the frontend call /api/v1/* on
// its own origin (no CORS) when NEXT_PUBLIC_API_URL is not set directly.
const BACKEND = process.env.API_INTERNAL_URL || "http://localhost:8000/api/v1";

async function forward(req: NextRequest, params: { proxy: string[] }) {
  const path = params.proxy.join("/");
  const url = `${BACKEND}/${path}${req.nextUrl.search}`;
  const headers = new Headers(req.headers);
  headers.delete("host");
  const res = await fetch(url, {
    method: req.method,
    headers,
    body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
    redirect: "manual",
  });
  return new NextResponse(res.body, { status: res.status, headers: res.headers });
}

export async function GET(req: NextRequest, ctx: { params: { proxy: string[] } }) {
  return forward(req, ctx.params);
}
export async function POST(req: NextRequest, ctx: { params: { proxy: string[] } }) {
  return forward(req, ctx.params);
}
export async function DELETE(req: NextRequest, ctx: { params: { proxy: string[] } }) {
  return forward(req, ctx.params);
}
