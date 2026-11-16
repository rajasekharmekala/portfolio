#!/usr/bin/env python3
"""CLI helper to inspect, place, modify, and verify Zerodha Kite GTT orders via Chrome Apple Events."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

CHROME_CTL_DIR = Path.home() / ".agents" / "skills" / "macos-browser-automation" / "scripts"
GTT_URL = "https://kite.zerodha.com/orders/gtt"
TAB_MATCH = "kite.zerodha.com/orders/gtt"


def _load_chrome_ctl():
    if not CHROME_CTL_DIR.exists():
        raise RuntimeError(
            f"Required dependency not found: {CHROME_CTL_DIR}. "
            "Install the 'macos-browser-automation' skill first."
        )
    sys.path.insert(0, str(CHROME_CTL_DIR))
    import chrome_ctl  # type: ignore
    return chrome_ctl


def round_tick(value: float, tick: float = 0.05) -> float:
    """Round price to nearest NSE/BSE tick size (default ₹0.05)."""
    return round(round(value / tick) * tick, 2)


def _write_output(data: Any, output_path: str | None) -> None:
    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote output to: {out}")
    else:
        print(json.dumps(data, indent=2))


def ensure_gtt_tab(chrome_ctl) -> dict[str, Any]:
    """Verify Chrome Apple Events JS is enabled and a Kite GTT tab is available."""
    status = chrome_ctl.check_status()
    if not status.get("ok"):
        raise RuntimeError(status.get("message", "Chrome Apple Events JS is not enabled."))
    tabs = chrome_ctl.list_tabs(TAB_MATCH)
    if not tabs:
        kite_tabs = chrome_ctl.list_tabs("kite.zerodha.com")
        if kite_tabs:
            chrome_ctl.navigate(GTT_URL, match="kite.zerodha.com")
        else:
            chrome_ctl.navigate(GTT_URL, new_tab=True)
        time.sleep(2.0)
        tabs = chrome_ctl.list_tabs(TAB_MATCH)
    if not tabs:
        raise RuntimeError("Could not open or locate https://kite.zerodha.com/orders/gtt in Chrome.")
    return {"ok": True, "tab": tabs[0]}


def list_gtts(chrome_ctl) -> dict[str, Any]:
    """Read all rows currently displayed in the Kite GTT table."""
    js = """(() => {
        const rows = Array.from(document.querySelectorAll("table tbody tr")).map((tr, idx) => {
            const cells = Array.from(tr.querySelectorAll("td")).map(td => td.innerText.trim().replace(/\\s+/g, " "));
            return {
                row_index: idx,
                created_on: cells[1] || "",
                instrument: cells[2] || "",
                type: cells[3] || "",
                trigger: cells[4] || "",
                ltp: cells[6] || "",
                qty: cells[7] || "",
                status: cells[8] || "",
                raw: cells
            };
        });
        return JSON.stringify({
            url: window.location.href,
            header: document.querySelector("h1, h2, .page-title")?.innerText?.trim() || "",
            count: rows.length,
            rows
        });
    })()"""
    raw = chrome_ctl.execute_js(js, match=TAB_MATCH)
    return json.loads(raw)


def _norm_symbol(instrument_cell: str) -> str:
    """Normalize 'PROV-SM NSE' or 'SAILIFE NSE' -> 'PROV' / 'SAILIFE'."""
    sym = instrument_cell.strip().split()[0] if instrument_cell.strip() else ""
    return re.sub(r"-(SM|BE|BZ)$", "", sym, flags=re.IGNORECASE).upper()


def _find_existing_active(rows: list[dict[str, Any]], symbol: str, side: str) -> dict[str, Any] | None:
    target_sym = re.sub(r"-(SM|BE|BZ)$", "", symbol.strip(), flags=re.IGNORECASE).upper()
    target_side = side.upper()
    for row in rows:
        if row.get("status", "").upper() != "ACTIVE":
            continue
        if _norm_symbol(row.get("instrument", "")) == target_sym and target_side in row.get("type", "").upper():
            return row
    return None


def _close_modals(chrome_ctl) -> None:
    chrome_ctl.execute_js(
        """(() => {
            document.querySelector(".gtt-window button.cancel")?.click();
            document.querySelector(".market-depth-widget button.button-outline")?.click();
        })()""",
        match=TAB_MATCH,
    )
    time.sleep(0.3)


def _open_edit_modal(chrome_ctl, row_index: int) -> bool:
    """Open the edit GTT modal for an existing table row."""
    js = f"""(() => {{
        const tr = document.querySelectorAll("table tbody tr")[{row_index}];
        if (!tr) return false;
        tr.dispatchEvent(new MouseEvent("mouseenter", {{bubbles: true}}));
        const menuBtn = tr.querySelector(".context-menu-button, .icon-ellipsis, button[aria-label*=option i], td:last-child button, td:last-child span");
        if (menuBtn) menuBtn.click();
        return true;
    }})()"""
    chrome_ctl.execute_js(js, match=TAB_MATCH)
    time.sleep(0.4)
    clicked = chrome_ctl.execute_js(
        """(() => {
            const items = Array.from(document.querySelectorAll(".context-menu li, .su-dropdown-menu li, .dropdown-menu li, a, button"));
            const editEl = items.find(el => /^edit$/i.test(el.innerText.trim()) && el.offsetParent !== null);
            if (!editEl) return false;
            editEl.click();
            return true;
        })()""",
        match=TAB_MATCH,
    )
    time.sleep(0.6)
    return str(clicked).lower() == "true"


def _delete_existing_row(chrome_ctl, row_index: int) -> bool:
    """Delete an existing GTT row via its row context menu."""
    js = f"""(() => {{
        const tr = document.querySelectorAll("table tbody tr")[{row_index}];
        if (!tr) return false;
        tr.dispatchEvent(new MouseEvent("mouseenter", {{bubbles: true}}));
        const menuBtn = tr.querySelector(".context-menu-button, .icon-ellipsis, button[aria-label*=option i], td:last-child button, td:last-child span");
        if (menuBtn) menuBtn.click();
        return true;
    }})()"""
    chrome_ctl.execute_js(js, match=TAB_MATCH)
    time.sleep(0.4)
    clicked = chrome_ctl.execute_js(
        """(() => {
            const items = Array.from(document.querySelectorAll(".context-menu li, .su-dropdown-menu li, .dropdown-menu li, a, button"));
            const delEl = items.find(el => /^delete$/i.test(el.innerText.trim()) && el.offsetParent !== null);
            if (!delEl) return false;
            delEl.click();
            return true;
        })()""",
        match=TAB_MATCH,
    )
    if str(clicked).lower() != "true":
        return False
    time.sleep(0.4)
    chrome_ctl.execute_js(
        """(() => {
            const confirmBtn = Array.from(document.querySelectorAll(".su-modal button")).find(b => /delete|confirm|yes|ok/i.test(b.innerText.trim()) && b.offsetParent !== null);
            confirmBtn?.click();
        })()""",
        match=TAB_MATCH,
    )
    time.sleep(1.0)
    return True


def _fill_and_submit_gtt_modal(
    chrome_ctl,
    symbol: str,
    qty: int,
    trigger: float,
    price: float,
    side: str,
    sme_one_lot: bool,
) -> dict[str, Any]:
    """Select Limit order in .gtt-window, fill trigger/qty/price, validate SME lot size, and submit."""
    side_val = side.upper()
    chrome_ctl.execute_js(
        f'document.querySelector(".gtt-window input[name=txType][value={side_val}]")?.click()',
        match=TAB_MATCH,
    )
    time.sleep(0.2)
    chrome_ctl.execute_js(
        'document.querySelector(".gtt-window input[value=LIMIT]")?.click()',
        match=TAB_MATCH,
    )
    time.sleep(0.4)

    def _fill(target_qty: int) -> dict[str, Any]:
        js_fill = f"""(() => {{
            const m = document.querySelector(".gtt-window");
            if (!m) return JSON.stringify({{error: "GTT modal (.gtt-window) did not open"}});
            const nums = m.querySelectorAll("input[type=number]");
            if (nums.length < 4) return JSON.stringify({{error: "Expected 4 numeric inputs in GTT modal", found: nums.length}});
            const setVal = (el, v) => {{
                el.focus();
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                setter.call(el, String(v));
                el.dispatchEvent(new Event("input", {{bubbles: true}}));
                el.dispatchEvent(new Event("change", {{bubbles: true}}));
                el.blur();
            }};
            setVal(nums[0], {trigger});
            setVal(nums[2], {target_qty});
            setVal(nums[3], {price});
            const invalids = Array.from(m.querySelectorAll("input:invalid")).map(e => ({{
                val: e.value,
                min: e.min || null,
                step: e.step || null,
                msg: e.validationMessage
            }}));
            return JSON.stringify({{
                header: m.querySelector("header, .header")?.innerText?.trim().replace(/\\s+/g, " ") || "",
                trigger: nums[0].value,
                qty: nums[2].value,
                price: nums[3].value,
                priceDisabled: nums[3].disabled,
                invalids
            }});
        }})()"""
        return json.loads(chrome_ctl.execute_js(js_fill, match=TAB_MATCH))

    filled = _fill(qty)
    if filled.get("error"):
        _close_modals(chrome_ctl)
        return {"symbol": symbol, "status": "error", "details": filled}

    invalids = filled.get("invalids") or []
    if invalids:
        min_qty = None
        for inv in invalids:
            if inv.get("min") and str(inv["min"]).isdigit():
                min_qty = int(inv["min"])
                break
            m = re.search(r"greater than or equal to\s+(\d+)", inv.get("msg", ""))
            if m:
                min_qty = int(m.group(1))
                break

        if sme_one_lot and min_qty and min_qty > qty:
            filled = _fill(min_qty)
            if filled.get("invalids"):
                _close_modals(chrome_ctl)
                return {"symbol": symbol, "status": "invalid", "details": filled}
            qty = min_qty
        else:
            _close_modals(chrome_ctl)
            return {
                "symbol": symbol,
                "status": "sme_lot_required" if min_qty else "invalid",
                "requested_qty": qty,
                "min_qty": min_qty,
                "adjusted_notional": round(min_qty * price, 2) if min_qty else None,
                "details": filled,
            }

    time.sleep(0.3)
    chrome_ctl.execute_js('document.querySelector(".gtt-window button.place")?.click()', match=TAB_MATCH)
    time.sleep(1.3)
    _close_modals(chrome_ctl)
    return {
        "symbol": symbol,
        "status": "placed",
        "qty": qty,
        "trigger": trigger,
        "price": price,
        "notional": round(qty * price, 2),
        "details": filled,
    }


def place_gtt(
    chrome_ctl,
    symbol: str,
    qty: int,
    trigger: float,
    price: float,
    exchange: str = "NSE",
    side: str = "BUY",
    on_existing: str = "modify",
    sme_one_lot: bool = False,
) -> dict[str, Any]:
    """Place, modify, or replace a single GTT order in Kite."""
    trig_r = round_tick(trigger)
    price_r = round_tick(price)

    current = list_gtts(chrome_ctl)
    existing = _find_existing_active(current.get("rows", []), symbol, side)
    action_taken = "created"

    if existing:
        if on_existing == "skip":
            return {"symbol": symbol, "status": "skipped_existing", "existing": existing}
        if on_existing == "modify":
            if _open_edit_modal(chrome_ctl, existing["row_index"]):
                res = _fill_and_submit_gtt_modal(chrome_ctl, symbol, qty, trig_r, price_r, side, sme_one_lot)
                res["action"] = "modified"
                return res
            # Fallback to replace if edit menu wasn't available
            on_existing = "replace"
        if on_existing == "replace":
            if not _delete_existing_row(chrome_ctl, existing["row_index"]):
                return {"symbol": symbol, "status": "error", "error": "Failed to delete existing GTT before replace", "existing": existing}
            action_taken = "replaced"

    # Open New GTT -> search -> select -> Create GTT
    chrome_ctl.execute_js('document.querySelector("button.create-new")?.click()', match=TAB_MATCH)
    time.sleep(0.5)
    js_search = f"""(() => {{
        const inp = document.querySelector(".market-depth-widget input[type=text]");
        if (!inp) return "no_inp";
        inp.focus();
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        setter.call(inp, {json.dumps(symbol)});
        inp.dispatchEvent(new Event("input", {{bubbles: true}}));
        return "typed";
    }})()"""
    if chrome_ctl.execute_js(js_search, match=TAB_MATCH) == "no_inp":
        _close_modals(chrome_ctl)
        return {"symbol": symbol, "status": "error", "error": "Search input not found in .market-depth-widget"}
    time.sleep(0.9)

    js_pick = f"""(() => {{
        const items = Array.from(document.querySelectorAll(".market-depth-widget li.results-item"));
        const symRe = new RegExp("^" + {json.dumps(symbol)} + "(\\\\b|-)", "i");
        let item = items.find(el => symRe.test(el.innerText.trim()) && el.innerText.includes({json.dumps(exchange.upper())}));
        if (!item) item = items.find(el => symRe.test(el.innerText.trim()));
        if (!item) return "no_match";
        item.click();
        return item.innerText.trim().replace(/\\s+/g, " ");
    }})()"""
    picked = chrome_ctl.execute_js(js_pick, match=TAB_MATCH)
    if picked == "no_match":
        _close_modals(chrome_ctl)
        return {"symbol": symbol, "status": "error", "error": f"Instrument '{symbol}' not found in Kite search"}
    time.sleep(0.7)

    chrome_ctl.execute_js(
        'Array.from(document.querySelectorAll(".market-depth-widget button")).find(b => b.innerText.trim() === "Create GTT")?.click()',
        match=TAB_MATCH,
    )
    time.sleep(0.7)

    res = _fill_and_submit_gtt_modal(chrome_ctl, symbol, qty, trig_r, price_r, side, sme_one_lot)
    res["picked"] = picked
    res["action"] = action_taken
    return res


def main() -> int:
    parser = argparse.ArgumentParser(description="Zerodha Kite GTT automation via Chrome Apple Events")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="Verify Chrome Apple Events and Kite GTT tab")
    p_check.add_argument("--output", help="Optional JSON output path")

    p_list = sub.add_parser("list", help="List current GTT rows from Kite")
    p_list.add_argument("--output", required=True, help="JSON output path")

    p_place = sub.add_parser("place", help="Place, modify, or replace a single GTT")
    p_place.add_argument("--symbol", required=True)
    p_place.add_argument("--qty", type=int, required=True)
    p_place.add_argument("--trigger", type=float, required=True)
    p_place.add_argument("--price", type=float, required=True)
    p_place.add_argument("--exchange", default="NSE", choices=["NSE", "BSE"])
    p_place.add_argument("--side", default="BUY", choices=["BUY", "SELL"])
    p_place.add_argument("--on-existing", default="modify", choices=["modify", "replace", "skip"])
    p_place.add_argument("--sme-one-lot", action="store_true")
    p_place.add_argument("--output", required=True, help="JSON output path")

    p_batch = sub.add_parser("batch", help="Place a JSON list of GTT specs sequentially and verify")
    p_batch.add_argument("--spec", required=True, help="Path to JSON array of {symbol, qty, trigger, price, exchange?, side?}")
    p_batch.add_argument("--on-existing", default="modify", choices=["modify", "replace", "skip"])
    p_batch.add_argument("--sme-one-lot", action="store_true")
    p_batch.add_argument("--output", required=True, help="JSON output path")

    args = parser.parse_args()
    try:
        chrome_ctl = _load_chrome_ctl()
        tab_info = ensure_gtt_tab(chrome_ctl)

        if args.cmd == "check":
            _write_output(tab_info, args.output)
            return 0

        if args.cmd == "list":
            data = list_gtts(chrome_ctl)
            _write_output(data, args.output)
            return 0

        if args.cmd == "place":
            res = place_gtt(
                chrome_ctl,
                symbol=args.symbol,
                qty=args.qty,
                trigger=args.trigger,
                price=args.price,
                exchange=args.exchange,
                side=args.side,
                on_existing=args.on_existing,
                sme_one_lot=args.sme_one_lot,
            )
            _write_output(res, args.output)
            return 0 if res.get("status") in ("placed", "skipped_existing") else 1

        if args.cmd == "batch":
            specs = json.loads(Path(args.spec).read_text(encoding="utf-8"))
            results = []
            for item in specs:
                res = place_gtt(
                    chrome_ctl,
                    symbol=item["symbol"],
                    qty=int(item["qty"]),
                    trigger=float(item["trigger"]),
                    price=float(item.get("price", item["trigger"])),
                    exchange=item.get("exchange", "NSE"),
                    side=item.get("side", "BUY"),
                    on_existing=item.get("on_existing", args.on_existing),
                    sme_one_lot=bool(item.get("sme_one_lot", args.sme_one_lot)),
                )
                results.append(res)
                time.sleep(1.0)
            verified = list_gtts(chrome_ctl)
            _write_output({"results": results, "verified_table": verified}, args.output)
            return 0

    except Exception as exc:
        err = {"ok": False, "error": str(exc)}
        if getattr(args, "output", None):
            _write_output(err, args.output)
        else:
            print(json.dumps(err, indent=2), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
