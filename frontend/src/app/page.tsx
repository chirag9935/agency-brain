"use client";
import { useState } from "react";
import { supabase } from "@/lib/supabase";

const API = process.env.NEXT_PUBLIC_API_URL;

type Proposal = {
  scope: string;
  deliverables: string[];
  timeline: string;
  price_range: string;
  assumptions: string[];
  source_chunk_ids: string[];
};

export default function Home() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(null);
  const [brief, setBrief] = useState("");
const [proposal, setProposal] = useState<Proposal | null>(null);
  const [status, setStatus] = useState("");

  async function login() {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) return setStatus(error.message);
    setToken(data.session.access_token);
    setStatus("Logged in");
  }

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    const form = new FormData();
    form.append("file", file);
    setStatus("Uploading...");
    const res = await fetch(`${API}/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const json = await res.json();
    setStatus(res.ok ? `Uploaded: ${json.chunks_created} chunks` : json.detail);
  }

  async function generate() {
    if (!token) return;
    setStatus("Generating...");
    setProposal(null);
    const res = await fetch(`${API}/proposal`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ brief }),
    });
    const json = await res.json();
    if (!res.ok) return setStatus(json.detail);
    setProposal(json);
    setStatus("Done");
  }

  if (!token) {
    return (
      <main className="max-w-md mx-auto p-8 space-y-3">
        <h1 className="text-2xl font-bold">AgencyBrain</h1>
        <input className="border p-2 w-full" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
        <input className="border p-2 w-full" type="password" placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
        <button className="bg-black text-white px-4 py-2" onClick={login}>Log in</button>
        <p className="text-sm text-gray-600">{status}</p>
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto p-8 space-y-4">
      <h1 className="text-2xl font-bold">AgencyBrain</h1>
      <input type="file" accept=".pdf,.docx" onChange={upload} />
      <textarea className="border p-2 w-full h-32" placeholder="Paste the client brief..." onChange={(e) => setBrief(e.target.value)} />
      <button className="bg-black text-white px-4 py-2" onClick={generate}>Generate proposal</button>
      <p className="text-sm text-gray-600">{status}</p>
      {proposal && (
        <section className="border p-4 space-y-2">
          <h2 className="font-semibold">Scope</h2><p>{proposal.scope}</p>
          <h2 className="font-semibold">Deliverables</h2>
          <ul className="list-disc pl-5">{proposal.deliverables.map((d: string) => <li key={d}>{d}</li>)}</ul>
          <h2 className="font-semibold">Timeline</h2><p>{proposal.timeline}</p>
          <h2 className="font-semibold">Price range</h2><p>{proposal.price_range}</p>
          <h2 className="font-semibold">Assumptions</h2>
          <ul className="list-disc pl-5">{proposal.assumptions.map((a: string) => <li key={a}>{a}</li>)}</ul>
          <p className="text-xs text-gray-500">Sources: {proposal.source_chunk_ids.length} chunks</p>
        </section>
      )}
    </main>
  );
}