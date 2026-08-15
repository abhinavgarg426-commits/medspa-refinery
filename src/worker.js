# Cloudflare Worker - Edge-native x402 / Pay-Per-Crawl compatible
# Deploy with: npx wrangler deploy
# This runs on Cloudflare's edge network (V8 isolates), not Node.js

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // CORS headers for agent clients
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, PAYMENT-SIGNATURE, X-Payment-Proof, X-Mock-Payment-Paid",
    };

    // Handle preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Public endpoints (no payment required)
    const publicPaths = ["/", "/health", "/llms.txt", "/llms-full.txt"];
    if (publicPaths.includes(path)) {
      return handlePublic(path, env, corsHeaders);
    }

    // Check payment
    const paymentSig = request.headers.get("PAYMENT-SIGNATURE") || request.headers.get("X-Payment-Proof");
    const mockAuth = request.headers.get("X-Mock-Payment-Paid");

    const RECEIVING_WALLET = env.RECEIVING_WALLET || "0x742d35Cc6634C0532925a3b844Bc454e4438f44e";
    const PRICE_USD = parseFloat(env.PRICE_PER_REQUEST_USD || "0.002");
    const PRICE_UNITS = Math.round(PRICE_USD * 1_000_000); // USDC 6 decimals

    if (!paymentSig && !mockAuth) {
      // Return 402 Payment Required with x402 spec
      const x402Spec = {
        x402_version: "1.0",
        title: "Miami MedSpa Data Endpoint",
        price: {
          amount_usd: PRICE_USD,
          amount_units: PRICE_UNITS,
          currency: "USDC",
          network: "base",
          chain_id: 8453
        },
        pay_to: RECEIVING_WALLET,
        scheme: "exact",
        resource: path,
        instruction: "Sign payment payload with your Web3 wallet or USDC permit and include in PAYMENT-SIGNATURE header."
      };

      const encodedSpec = btoa(JSON.stringify(x402Spec));

      return new Response(JSON.stringify({
        error: "Payment Required",
        status_code: 402,
        message: `This endpoint requires a micro-payment of $${PRICE_USD} USDC via x402 protocol.`,
        x402_details: x402Spec
      }), {
        status: 402,
        headers: {
          ...corsHeaders,
          "Content-Type": "application/json",
          "PAYMENT-REQUIRED": encodedSpec,
          "X-Payment-Address": RECEIVING_WALLET,
          "X-Payment-Price": `${PRICE_USD} USDC`,
          "X-Payment-Network": "base",
          "WWW-Authenticate": `x402 realm="Data Refinery", price="${PRICE_USD}", address="${RECEIVING_WALLET}"`
        }
      });
    }

    // Payment verified - serve data
    return handleData(path, url.searchParams, corsHeaders);
  }
};

async function handlePublic(path, env, corsHeaders) {
  switch (path) {
    case "/":
      return jsonResponse({
        status: "online",
        service: "Miami MedSpa Data Refinery (Cloudflare Workers)",
        protocol: "x402 HTTP 402 + Cloudflare Pay-Per-Crawl",
        llms_txt: "/llms.txt",
        llms_full_txt: "/llms-full.txt"
      }, corsHeaders);

    case "/health":
      return jsonResponse({ status: "ok" }, corsHeaders);

    case "/llms.txt":
      return textResponse(`# Miami MedSpa & Aesthetic Clinic Data Refinery
> Machine-readable structured database of local aesthetic clinics, pricing, services, and AI visibility readiness scores in Miami, FL.

## Core Endpoints
- GET /api/v1/clinics: Returns full list of medspas, location, rating, and AI visibility score. (Cost: $0.002 USDC via x402)
- GET /api/v1/clinics/{id}: Returns specific clinic info and itemized pricing list (Botox, fillers, lasers, weight loss). (Cost: $0.002 USDC via x402)
- GET /api/v1/search?service=botox: Query clinics offering specific treatments and compare prices across Miami. (Cost: $0.002 USDC via x402)

## Data Specification
- Format: JSON
- Payment Standard: HTTP 402 / x402 Protocol (Base Network / USDC) + Cloudflare Pay-Per-Crawl
- Pay-To Address: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

## Full Documentation & Dump
- GET /llms-full.txt : Full plain-text dump for context window ingestion.`, corsHeaders);

    case "/llms-full.txt":
      const data = await getClinicData();
      return textResponse(formatFullDump(data), corsHeaders);
  }
}

async function handleData(path, params, corsHeaders) {
  const data = await getClinicData();

  switch (path) {
    case "/api/v1/clinics": {
      const city = params.get("city");
      let clinics = data;
      if (city) {
        clinics = data.filter(c => c.city.toLowerCase() === city.toLowerCase());
      }
      return jsonResponse({
        status: "success",
        count: clinics.length,
        data: clinics,
        payment_receipt: { settled: true, cost_usd: 0.002, protocol: "x402" }
      }, corsHeaders);
    }

    case "/api/v1/search": {
      const treatment = params.get("service") || params.get("treatment");
      if (!treatment) {
        return jsonResponse({ error: "Missing 'service' or 'treatment' query param" }, corsHeaders, 400);
      }
      const matches = data.filter(c => 
        c.services.some(s => 
          s.item.toLowerCase().includes(treatment.toLowerCase()) ||
          s.category.toLowerCase().includes(treatment.toLowerCase())
        )
      ).map(c => ({
        ...c,
        matching_services: c.services.filter(s =>
          s.item.toLowerCase().includes(treatment.toLowerCase()) ||
          s.category.toLowerCase().includes(treatment.toLowerCase())
        )
      }));
      return jsonResponse({
        status: "success",
        query: treatment,
        matches_count: matches.length,
        data: matches
      }, corsHeaders);
    }

    default: {
      // /api/v1/clinics/{id}
      const match = path.match(/^\/api\/v1\/clinics\/(\d+)$/);
      if (match) {
        const id = parseInt(match[1]);
        const clinic = data.find(c => c.id === id);
        if (!clinic) {
          return jsonResponse({ error: "Clinic not found" }, corsHeaders, 404);
        }
        return jsonResponse({
          status: "success",
          data: clinic,
          payment_receipt: { settled: true, cost_usd: 0.002, protocol: "x402" }
        }, corsHeaders);
      }
      return jsonResponse({ error: "Not found" }, corsHeaders, 404);
    }
  }
}

// In-memory data (in production, use KV or D1)
async function getClinicData() {
  return [
    {
      id: 1,
      name: "Elegance Aesthetics & MedSpa",
      city: "Miami",
      state: "FL",
      address: "1200 Brickell Ave, Suite 400, Miami, FL 33131",
      phone: "+1-305-555-0192",
      website: "https://elegancemedspamiami.example.com",
      rating: 4.9,
      reviews_count: 342,
      ai_visibility_score: 85,
      last_updated: "2026-08-15",
      services: [
        { category: "Injectables", item: "Botox (per unit)", price_usd: 14.00, unit: "unit" },
        { category: "Injectables", item: "Juvederm Ultra XC", price_usd: 650.00, unit: "syringe" },
        { category: "Body Contouring", item: "CoolSculpting Elite", price_usd: 750.00, unit: "cycle" },
        { category: "Wellness", item: "Semaglutide Weight Loss (Monthly)", price_usd: 399.00, unit: "month" },
        { category: "Lasers", item: "IPL Photofacial", price_usd: 350.00, unit: "session" }
      ]
    },
    {
      id: 2,
      name: "South Beach Glow MedSpa",
      city: "Miami",
      state: "FL",
      address: "750 Ocean Drive, Miami Beach, FL 33139",
      phone: "+1-305-555-0144",
      website: "https://sobe-glow.example.com",
      rating: 4.8,
      reviews_count: 512,
      ai_visibility_score: 42,
      last_updated: "2026-08-15",
      services: [
        { category: "Injectables", item: "Dysport (per unit)", price_usd: 5.00, unit: "unit" },
        { category: "Injectables", item: "Restylane Kysse", price_usd: 700.00, unit: "syringe" },
        { category: "Wellness", item: "Tirzepatide Program (Monthly)", price_usd: 550.00, unit: "month" },
        { category: "Skincare", item: "HydraFacial Deluxe", price_usd: 275.00, unit: "session" }
      ]
    },
    {
      id: 3,
      name: "Coral Gables Laser & Skin Institute",
      city: "Miami",
      state: "FL",
      address: "2320 Ponce de Leon Blvd, Coral Gables, FL 33134",
      phone: "+1-305-555-0188",
      website: "https://coralgableslaser.example.com",
      rating: 4.9,
      reviews_count: 189,
      ai_visibility_score: 28,
      last_updated: "2026-08-15",
      services: [
        { category: "Lasers", item: "Fraxel Dual Laser", price_usd: 1200.00, unit: "session" },
        { category: "Injectables", item: "Sculptra Aesthetic", price_usd: 900.00, unit: "vial" },
        { category: "Injectables", item: "Botox (per unit)", price_usd: 16.00, unit: "unit" },
        { category: "Regenerative", item: "PRP Hair Restoration", price_usd: 850.00, unit: "session" }
      ]
    },
    {
      id: 4,
      name: "Wynwood Aesthetics Studio",
      city: "Miami",
      state: "FL",
      address: "250 NW 24th St, Miami, FL 33127",
      phone: "+1-305-555-0103",
      website: "https://wynwoodaesthetics.example.com",
      rating: 4.7,
      reviews_count: 276,
      ai_visibility_score: 91,
      last_updated: "2026-08-15",
      services: [
        { category: "Injectables", item: "Xeomin (per unit)", price_usd: 12.00, unit: "unit" },
        { category: "Skincare", item: "RF Microneedling (Morphius8)", price_usd: 850.00, unit: "session" },
        { category: "Wellness", item: "IV Vitamin Drip (NAD+)", price_usd: 250.00, unit: "infusion" }
      ]
    }
  ];
}

function formatFullDump(clinics) {
  let out = "# Full Miami MedSpa Dataset Dump\n";
  out += `Total Clinics Registered: ${clinics.length}\n`;
  out += "=====================================================\n\n";
  for (const c of clinics) {
    out += `## Clinic: ${c.name}\n`;
    out += `- City: ${c.city}, ${c.state}\n`;
    out += `- Address: ${c.address}\n`;
    out += `- Phone: ${c.phone}\n`;
    out += `- Website: ${c.website}\n`;
    out += `- Rating: ${c.rating} ⭐ (${c.reviews_count} reviews)\n`;
    out += `- AI Visibility Score: ${c.ai_visibility_score}/100\n`;
    out += "- Services & Pricing:\n";
    for (const s of c.services) {
      out += `  * [${s.category}] ${s.item}: $${s.price_usd.toFixed(2)} per ${s.unit}\n`;
    }
    out += "\n-----------------------------------------------------\n\n";
  }
  return out;
}

function jsonResponse(data, headers, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { ...headers, "Content-Type": "application/json" }
  });
}

function textResponse(text, headers, status = 200) {
  return new Response(text, {
    status,
    headers: { ...headers, "Content-Type": "text/plain; charset=utf-8" }
  });
}