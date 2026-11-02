// GitHub Copilot Desktop Extension: Voice Companion HUD
// Connects GitHub Copilot Desktop with the voice-bridge daemon.
// Exposes the Ambient Floating HUD Canvas and voice controls.

// CRITICAL: Extensions communicate with Copilot runtime via JSON-RPC over stdout.
// Any plain text written to stdout corrupts JSON-RPC framing and drops the connection.
// Route all stdout logging to stderr so logs are preserved safely without breaking RPC.
console.log = (...args) => console.error(...args);
console.info = (...args) => console.error(...args);
console.debug = (...args) => console.error(...args);

process.on("unhandledRejection", (reason) => {
  console.error("[Voice Companion] Unhandled rejection:", reason);
});
process.on("uncaughtException", (err) => {
  console.error("[Voice Companion] Uncaught exception:", err);
});

let sdk;
try {
  sdk = await import("@github/copilot-sdk/extension");
} catch {
  sdk = await import("/Applications/GitHub Copilot.app/Contents/Resources/copilot-sdk/extension.js");
}

const { joinSession, createCanvas } = sdk;

const BRIDGE_BASE = process.env.VB_URL || "http://127.0.0.1:4747";

async function bridgeFetch(path, options = {}) {
  try {
    const res = await fetch(`${BRIDGE_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Client": "copilot-desktop-extension",
        ...(options.headers || {}),
      },
      signal: AbortSignal.timeout( options.timeoutMs || 10000 ),
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

// 1. Register the Ambient Floating HUD Canvas
const voiceCanvas = createCanvas({
  id: "voice-companion",
  displayName: "Voice Companion HUD",
  description: "Ambient status HUD, live audio visualizer, and hands-free microphone controls for GitHub Copilot Desktop",
  open: async (ctx) => {
    return {
      url: `${BRIDGE_BASE}/hud`,
      title: "Voice Companion HUD",
      status: "Live",
    };
  },
  actions: [
    {
      name: "toggle_mute",
      description: "Toggle microphone mute / unmute state",
      handler: async () => {
        const res = await bridgeFetch("/api/handsfree/toggle", { method: "POST" });
        return res.data || { ok: res.ok };
      },
    },
    {
      name: "stop_speech",
      description: "Stop current spoken audio playback immediately",
      handler: async () => {
        const res = await bridgeFetch("/api/stop", { method: "POST" });
        return res.data || { ok: res.ok };
      },
    },
    {
      name: "set_voice",
      description: "Switch active spoken voice (e.g. alloy, echo, shimmer, marin, cedar)",
      inputSchema: {
        type: "object",
        properties: {
          voice: { type: "string", description: "Voice identifier" },
        },
        required: ["voice"],
      },
      handler: async (ctx) => {
        const voice = ctx.input?.voice;
        if (!voice) return { error: "voice name is required" };
        const res = await bridgeFetch("/api/settings", {
          method: "PUT",
          body: JSON.stringify({ tts: { voice } }),
        });
        return res.data || { ok: res.ok };
      },
    },
  ],
});

// 2. Register Agent-callable Copilot Tools
const tools = [
  {
    name: "voice_companion_open",
    description: "Open or focus the Voice Companion Ambient HUD canvas with real-time waveform visualizer and voice status in Copilot Desktop",
    parameters: {
      type: "object",
      properties: {},
    },
    handler: async () => {
      const health = await bridgeFetch("/api/health");
      return JSON.stringify({
        canvasId: "voice-companion",
        hudUrl: `${BRIDGE_BASE}/hud`,
        bridgeOnline: health.ok,
        status: health.ok ? "Voice Companion is running. Use the canvas or open the HUD in a side panel." : "Voice bridge daemon is not running.",
      });
    },
  },
  {
    name: "voice_speak",
    description: "Speak a brief message, announcement, or summary aloud to the developer using natural vocal prosody",
    parameters: {
      type: "object",
      properties: {
        text: { type: "string", description: "The text to speak aloud" },
        voice: { type: "string", description: "Optional voice override (alloy, echo, shimmer, etc.)" },
      },
      required: ["text"],
    },
    handler: async (args) => {
      if (!args.text) return "No text provided to speak.";
      const res = await bridgeFetch("/api/speak", {
        method: "POST",
        body: JSON.stringify({ text: args.text, voice: args.voice }),
      });
      if (!res.ok) return `Could not speak: ${res.error || res.data?.error || "Bridge unavailable"}`;
      return `Spoke aloud: "${args.text.slice(0, 80)}${args.text.length > 80 ? "..." : ""}"`;
    },
  },
  {
    name: "voice_mute",
    description: "Mute or unmute the Voice Companion hands-free microphone listening",
    parameters: {
      type: "object",
      properties: {
        muted: { type: "boolean", description: "True to mute, false to unmute. Omit to toggle." },
      },
    },
    handler: async (args) => {
      let res;
      if (args.muted === undefined) {
        res = await bridgeFetch("/api/handsfree/toggle", { method: "POST" });
      } else {
        res = await bridgeFetch("/api/handsfree", {
          method: "POST",
          body: JSON.stringify({ on: !args.muted }),
        });
      }
      if (!res.ok) return `Failed to update microphone: ${res.error || "Bridge unavailable"}`;
      const isMuted = !res.data?.on || res.data?.mutedByUser;
      return `Microphone is now ${isMuted ? "MUTED" : "LISTENING (unmuted)"}.`;
    },
  },
  {
    name: "voice_status",
    description: "Query current Voice Companion status, active playback, microphone, and connected clients",
    parameters: {
      type: "object",
      properties: {},
    },
    handler: async () => {
      const [healthRes, stateRes] = await Promise.all([
        bridgeFetch("/api/health"),
        bridgeFetch("/api/state"),
      ]);
      if (!healthRes.ok) return "Voice bridge is currently OFFLINE.";
      const s = stateRes.data || {};
      return JSON.stringify({
        online: true,
        voiceEnabled: s.settings?.voice?.enabled !== false,
        speaking: Boolean(s.speaker?.speaking || s.orator?.state === "speaking" || s.reader?.state === "playing"),
        micListening: Boolean(s.handsfree?.on && !s.handsfree?.mutedByUser),
        micMuted: Boolean(!s.handsfree?.on || s.handsfree?.mutedByUser),
        activeVoice: s.settings?.tts?.voice || "alloy",
        clients: healthRes.data?.clients,
        lastUtterance: s.lastUtterance || null,
        hudUrl: `${BRIDGE_BASE}/hud`,
      }, null, 2);
    },
  },
  {
    name: "voice_last_turn",
    description: "Retrieve the developer's most recent ambient spoken utterance captured by the Voice Companion microphone",
    parameters: {
      type: "object",
      properties: {},
    },
    handler: async () => {
      const res = await bridgeFetch("/api/last_turn");
      if (!res.ok) return "Could not reach Voice Companion.";
      if (!res.data?.text) return "No speech captured recently.";
      return JSON.stringify(res.data, null, 2);
    },
  },
  {
    name: "voice_listen",
    description: "Listen for the user's spoken voice turn using the echo-cancelled microphone. Returns the transcribed text.",
    parameters: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "Optional short question to speak before listening" },
        timeoutSec: { type: "number", description: "Timeout in seconds to wait for user to speak (default 25)" },
      },
    },
    handler: async (args) => {
      const res = await bridgeFetch("/api/listen", {
        method: "POST",
        body: JSON.stringify({ prompt: args.prompt, timeoutSec: args.timeoutSec || 25 }),
        timeoutMs: ((args.timeoutSec || 25) + 5) * 1000,
      });
      if (!res.ok) return `Listening error: ${res.error || res.data?.error || "Bridge unavailable"}`;
      if (res.data?.status === 'replied') return `User said: "${res.data.userUtterance}"`;
      if (res.data?.status === 'timeout') return 'User did not speak within the timeout window.';
      return JSON.stringify(res.data);
    },
  },
];

// 3. Join the Copilot session
let session = null;
try {
  session = await joinSession({
    canvases: [voiceCanvas],
    tools,
  });
  console.log(`[Voice Companion] Attached to Copilot session: ${session?.sessionId}`);
} catch (err) {
  // If run outside an active Copilot extension host process, log cleanly
  console.error("Voice Companion extension initialized (waiting for session host):", err.message);
}

// 4. Two-Way Speech Bridge between Voice Bridge Daemon and Copilot Chat
let WSClient = globalThis.WebSocket;
if (!WSClient) {
  try {
    const wsModule = await import("ws");
    WSClient = wsModule.default || wsModule;
  } catch {}
}

const WS_BASE = BRIDGE_BASE.replace(/^http/, "ws") + "/ws";
let ws = null;
let reconnectTimer = null;
let lastDispatchedText = "";
let lastDispatchedAt = 0;
let pendingVoiceTurnId = null;

function setupBridgeListener(activeSession) {
  if (!activeSession || !WSClient) return;

  // Listen to Copilot assistant responses to speak aloud if the turn was voice-driven
  try {
    activeSession.on("assistant.message", async (evt) => {
      try {
        const content = evt?.data?.content;
        const originatingId = evt?.data?.originatingMessageId;
        if (content && (originatingId === pendingVoiceTurnId || (!originatingId && pendingVoiceTurnId))) {
          pendingVoiceTurnId = null;
          console.log(`[Voice Companion] Speaking Copilot response aloud (${content.length} chars)`);
          await bridgeFetch("/api/speak", {
            method: "POST",
            body: JSON.stringify({ text: content, role: "assistant" }),
          });
        }
      } catch (e) {
        console.error("[Voice Companion] Error in assistant.message speech handler:", e.message);
      }
    });
  } catch (err) {
    console.error("[Voice Companion] Failed to attach assistant.message listener:", err.message);
  }

  function connectWs() {
    if (ws && (ws.readyState === WSClient.OPEN || ws.readyState === WSClient.CONNECTING)) return;
    try {
      ws = new WSClient(WS_BASE);

      ws.onopen = () => {
        console.log("[Voice Companion] Connected to voice-bridge WebSocket");
        ws.send(JSON.stringify({ type: "hello", output: false, client: "copilot-desktop" }));
      };

      ws.onmessage = async (evt) => {
        try {
          const raw = typeof evt.data === "string" ? evt.data : evt.data?.toString?.();
          const msg = JSON.parse(raw);
          
          // Look for completed user speech turn
          if (msg.type === "turn_captured" || (msg.type === "turn" && msg.text)) {
            const text = (msg.text || "").trim();
            if (!text) return;

            const now = Date.now();
            if (text === lastDispatchedText && now - lastDispatchedAt < 2000) return;
            lastDispatchedText = text;
            lastDispatchedAt = now;

            console.log(`[Voice Companion] Spoken utterance captured: "${text}". Sending to Copilot chat...`);
            try {
              pendingVoiceTurnId = await activeSession.send(text);
              console.log(`[Voice Companion] Prompt admitted by Copilot session. messageId: ${pendingVoiceTurnId}`);
            } catch (sendErr) {
              console.error("[Voice Companion] activeSession.send() failed:", sendErr.message);
            }
          }
        } catch (err) {
          console.error("[Voice Companion] Error parsing bridge WS frame:", err.message);
        }
      };

      ws.onclose = () => {
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWs, 2000);
      };

      ws.onerror = () => {
        try { ws.close(); } catch {}
      };
    } catch (err) {
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectWs, 3000);
    }
  }

  connectWs();
}

if (session) {
  setupBridgeListener(session);
  // Keep the extension process event loop alive indefinitely
  setInterval(() => {}, 30000);
}
