from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/heatmap", response_class=HTMLResponse)
async def consensus_heatmap_page(
    topic: str = Query("Should we launch an AI note-taking app?", min_length=3, max_length=500),
):
    """
    Live consensus heatmap demo page.

    Connects to the existing simulation websocket and renders per-round pairwise
    agreement scores as a D3 color matrix.
    """
    topic_for_ws = topic.replace(" ", "_")

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Agentica • Consensus Heatmap</title>
    <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
    <style>
      :root {{
        --bg: #0b1020;
        --panel: #121a33;
        --text: #e7ecff;
        --muted: rgba(231, 236, 255, 0.7);
        --grid: rgba(231, 236, 255, 0.12);
      }}
      body {{
        margin: 0;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji",
          "Segoe UI Emoji";
        background: radial-gradient(1200px 600px at 10% 10%, #121a33 0%, var(--bg) 55%);
        color: var(--text);
      }}
      .wrap {{
        max-width: 1100px;
        margin: 28px auto;
        padding: 0 18px;
      }}
      .header {{
        display: grid;
        gap: 10px;
        margin-bottom: 14px;
      }}
      .title {{
        font-size: 20px;
        font-weight: 650;
        letter-spacing: 0.2px;
      }}
      .sub {{
        color: var(--muted);
        font-size: 13px;
        line-height: 1.4;
      }}
      .panel {{
        background: color-mix(in srgb, var(--panel) 92%, black);
        border: 1px solid rgba(231, 236, 255, 0.12);
        border-radius: 14px;
        padding: 14px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.35);
      }}
      .row {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }}
      .badge {{
        display: inline-flex;
        gap: 8px;
        align-items: center;
        padding: 7px 10px;
        border-radius: 999px;
        background: rgba(231, 236, 255, 0.06);
        border: 1px solid rgba(231, 236, 255, 0.12);
        font-size: 12px;
        color: var(--muted);
      }}
      .dot {{
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: #ff4d4d;
        box-shadow: 0 0 0 3px rgba(255, 77, 77, 0.16);
      }}
      .dot.on {{
        background: #47ff9a;
        box-shadow: 0 0 0 3px rgba(71, 255, 154, 0.16);
      }}
      .legend {{
        display: flex;
        gap: 10px;
        align-items: center;
        color: var(--muted);
        font-size: 12px;
      }}
      .legend-bar {{
        width: 180px;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #2b2d42, #2f6fed, #51ff9a);
        border: 1px solid rgba(231, 236, 255, 0.14);
      }}
      #chart {{
        width: 100%;
        overflow-x: auto;
      }}
      svg {{
        max-width: 100%;
        height: auto;
      }}
      .axis-label {{
        fill: rgba(231, 236, 255, 0.84);
        font-size: 11px;
      }}
      .cell {{
        stroke: var(--grid);
        stroke-width: 1px;
        shape-rendering: crispEdges;
      }}
      .tooltip {{
        position: fixed;
        pointer-events: none;
        z-index: 10;
        padding: 8px 10px;
        border-radius: 10px;
        background: rgba(18, 26, 51, 0.95);
        border: 1px solid rgba(231, 236, 255, 0.18);
        color: var(--text);
        font-size: 12px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.35);
        transform: translate(10px, 10px);
        opacity: 0;
        transition: opacity 80ms linear;
        white-space: nowrap;
      }}
      code {{
        color: rgba(231, 236, 255, 0.85);
      }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="header">
        <div class="title">Consensus Heatmap (real-time)</div>
        <div class="sub">
          Pairwise agreement score between all agents, updated after each simulation round.
          Connects to <code>/api/ws/simulate/&lt;topic&gt;</code> and listens for <code>consensus_heatmap</code>.
        </div>
      </div>

      <div class="panel">
        <div class="row">
          <div class="badge"><span id="connDot" class="dot"></span><span id="connText">disconnected</span></div>
          <div class="badge">topic: <span id="topicText"></span></div>
          <div class="badge">round: <span id="roundText">—</span></div>
          <div class="legend">
            low <span class="legend-bar"></span> high
          </div>
        </div>
        <div id="chart"></div>
      </div>
    </div>
    <div id="tooltip" class="tooltip"></div>

    <script>
      const topic = {topic!r};
      const topicForWs = {topic_for_ws!r};
      document.getElementById("topicText").textContent = topic;

      const tooltip = d3.select("#tooltip");
      const connDot = document.getElementById("connDot");
      const connText = document.getElementById("connText");
      const roundText = document.getElementById("roundText");

      const color = d3.scaleLinear()
        .domain([0.0, 0.5, 1.0])
        .range(["#2b2d42", "#2f6fed", "#51ff9a"]);

      function setConnected(on) {{
        connDot.classList.toggle("on", on);
        connText.textContent = on ? "connected" : "disconnected";
      }}

      function renderHeatmap(agents, matrix) {{
        const n = agents.length;
        const cell = 26;
        const leftPad = 140;
        const topPad = 120;
        const width = leftPad + n * cell + 20;
        const height = topPad + n * cell + 20;

        d3.select("#chart").selectAll("*").remove();
        const svg = d3.select("#chart")
          .append("svg")
          .attr("viewBox", `0 0 ${{width}} ${{height}}`)
          .attr("width", width)
          .attr("height", height);

        // Column labels (top)
        svg.append("g")
          .selectAll("text")
          .data(agents)
          .join("text")
          .attr("class", "axis-label")
          .attr("text-anchor", "start")
          .attr("transform", (d, i) => `translate(${{leftPad + i * cell + 6}}, ${{topPad - 10}}) rotate(-55)`)
          .text(d => d);

        // Row labels (left)
        svg.append("g")
          .selectAll("text")
          .data(agents)
          .join("text")
          .attr("class", "axis-label")
          .attr("text-anchor", "end")
          .attr("x", leftPad - 10)
          .attr("y", (d, i) => topPad + i * cell + cell * 0.7)
          .text(d => d);

        // Cells
        const rows = d3.range(n).flatMap(i => d3.range(n).map(j => ({{
          i, j,
          a: agents[i],
          b: agents[j],
          v: matrix[i][j]
        }})));

        svg.append("g")
          .selectAll("rect")
          .data(rows)
          .join("rect")
          .attr("class", "cell")
          .attr("x", d => leftPad + d.j * cell)
          .attr("y", d => topPad + d.i * cell)
          .attr("width", cell)
          .attr("height", cell)
          .attr("fill", d => color(d.v))
          .on("mousemove", (event, d) => {{
            tooltip
              .style("opacity", 1)
              .style("left", `${{event.clientX}}px`)
              .style("top", `${{event.clientY}}px`)
              .text(`${{d.a}} ↔ ${{d.b}}  agreement: ${{(d.v * 100).toFixed(1)}}%`);
          }})
          .on("mouseleave", () => tooltip.style("opacity", 0));
      }}

      function connectWs() {{
        const scheme = (location.protocol === "https:") ? "wss" : "ws";
        const wsUrl = `${{scheme}}://${{location.host}}/api/ws/simulate/${{topicForWs}}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => setConnected(true);
        ws.onclose = () => {{
          setConnected(false);
          setTimeout(connectWs, 800);
        }};
        ws.onerror = () => setConnected(false);

        ws.onmessage = (evt) => {{
          let msg;
          try {{ msg = JSON.parse(evt.data); }} catch {{ return; }}

          if (msg.type === "round_end") {{
            roundText.textContent = msg.round ?? "—";
          }}

          if (msg.type === "consensus_heatmap") {{
            roundText.textContent = msg.round ?? "—";
            if (Array.isArray(msg.agents) && Array.isArray(msg.matrix)) {{
              renderHeatmap(msg.agents, msg.matrix);
            }}
          }}
        }};
      }}

      connectWs();
    </script>
  </body>
</html>"""
    return HTMLResponse(content=html)

