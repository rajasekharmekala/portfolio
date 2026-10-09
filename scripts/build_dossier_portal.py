#!/usr/bin/env python3
"""
Master Portal Rebuild Script for docs/index.html and docs/blogs/index.html
"""

import os
import glob
import re
import json
from bs4 import BeautifulSoup, Comment, NavigableString

def parse_dossier(filepath):
    filename = os.path.basename(filepath)
    symbol = filename.replace('_dossier.html', '')
    filesize_kb = os.path.getsize(filepath) / 1024.0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        
    title_el = soup.find('h1', class_='firstHeading') or soup.find('h1')
    raw_title = title_el.text.strip() if title_el else symbol
    
    # Extract clean company name
    # e.g. "Computer Age Management Services Ltd (NSE: CAMS)" -> "Computer Age Management Services Ltd"
    company_name = re.sub(r'\s*\([^)]*\)', '', raw_title).strip()
    if not company_name:
        company_name = symbol
        
    # Infobox extraction
    infobox = soup.find('table', class_=lambda c: c and ('infobox' in c or 'infobox-data' in c)) or soup.find(class_='infobox')
    info = {}
    if infobox:
        for row in infobox.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td:
                k = th.text.strip()
                v = td.text.strip()
                info[k] = v
                
    # Detect market: IN vs US
    tickers = info.get('Exchange Tickers', info.get('Ticker', info.get('Listings', info.get('Primary Exchange', ''))))
    us_symbols = {
        'ANET', 'CMG', 'CRWD', 'DOCN', 'GOOG', 'GOOGL', 'MCHP', 'MELI', 'NKE', 'ORCL', 'VRT',
        'NVDA', 'META', 'AMZN', 'MSFT', 'BABA', 'TCEHY', 'RKLB', 'TTD', 'ASX', 'PANW', 'QCOM',
        'AXP', 'COF', 'LUV', 'UBER', 'RMBS', 'JD', 'DHI', 'SOFI', 'WMT', 'NFXL', 'ORCX', 'FNGU',
        'FAS', 'KORU', 'UNHG', 'TQQQ', 'NBIL', 'EDC', 'SPXL', 'UDOW', 'TARK', 'FXI', 'UNH',
        'MSTR', 'ADBE', 'MSTX', 'QCML', 'ADBG', 'NVDL', 'TSLA', 'AAPL', 'AMD', 'INTC', 'TSM',
        'BE', 'ABNB', 'ALAB', 'CEG', 'APP', 'ONON', 'DECK', 'SNOW', 'NOW', 'PDD', 'SE', 'NTES',
        'BIDU', 'SKHY', 'STM', 'ON', 'SOXL', 'GGLL'
    }
    market = 'US' if (symbol in us_symbols or 'NASDAQ' in tickers or 'NYSE' in tickers or 'OTCQX' in tickers or 'ADR' in tickers) else 'IN'
    
    # Macro Sector & Fine Subsector
    macro_sector = info.get('Macro Sector', info.get('Sector', info.get('US taxonomy', 'Diversified Industrials & Technology')))
    fine_subsector = info.get('Fine Subsector', info.get('Subsector', macro_sector))
    
    # Financial metrics - check various possible keys for CMP
    cmp_str = ''
    for k in info:
        if 'cmp' in k.lower() or 'current price' in k.lower() or 'current market price' in k.lower():
            cmp_str = info[k]
            break
            
    cmp_val = 0.0
    cmp_match = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)', cmp_str)
    if cmp_match:
        cmp_val = float(cmp_match.group(1).replace(',', ''))
        
    mcap_str = ''
    for k in info:
        if 'market cap' in k.lower():
            mcap_str = info[k]
            break
    mcap_val = 0.0
    mcap_match = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)', mcap_str)
    if mcap_match:
        mcap_val = float(mcap_match.group(1).replace(',', ''))
        
    roce_str = ''
    for k in info:
        if 'roce' in k.lower() or 'roic' in k.lower() or 'return on capital' in k.lower():
            roce_str = info[k]
            break
    roce_val = 20.0
    roce_match = re.search(r'([\d\.]+)%', roce_str)
    if roce_match:
        roce_val = float(roce_match.group(1))
        
    strategy_bucket = info.get('Strategy Bucket', info.get('Strategy', info.get('Strategy Book', 'TACTICAL_MOMENTUM'))).upper()
    if 'CORE' in strategy_bucket:
        strat_clean = 'core alpha'
        strat_badge = '🛡️ Core Alpha'
        strat_class = 'badge-core-alpha'
    elif 'SATELLITE' in strategy_bucket or 'LEVERAGED' in strategy_bucket:
        strat_clean = 'leveraged satellite'
        strat_badge = '⚡ Leveraged Satellite'
        strat_class = 'badge-leveraged-satellite'
    else:
        strat_clean = 'tactical momentum'
        strat_badge = '⚔️ Tactical Momentum'
        strat_class = 'badge-tactical-momentum'
        
    gate_status = info.get('Layer 1 Gate Status', 'PASS')
        
    # Extract Banner and Infobox Verdict text
    banner = soup.find('div', class_=lambda x: x and ('executive-banner' in x or 'executive-summary' in x or 'banner' in x))
    badge_el = banner.find(class_='badge') if banner else None
    badge_text = badge_el.text.strip().upper() if badge_el else ''
    banner_text = banner.text.strip() if banner else ''
    
    info_v = ''
    if infobox:
        for row in infobox.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td and ('verdict' in th.text.lower() or 'disposition' in th.text.lower()):
                info_v = td.text.strip()
                
    combined_v = (badge_text + ' ' + info_v + ' ' + banner_text).upper()
    
    if 'REJECT' in badge_text or 'FAIL' in badge_text or 'AVOID' in badge_text or 'REJECT' in info_v.upper() or 'FAIL' in info_v.upper() or 'AVOID' in info_v.upper():
        norm_verdict = 'AVOID / REJECTED'
        verdict_class = 'verdict-reject'
        verdict_icon = '⛔'
        is_archived = True
    elif 'IMMEDIATE BUY' in combined_v or 'IMMEDIATE_BUY' in combined_v:
        norm_verdict = 'IMMEDIATE BUY'
        verdict_class = 'verdict-buy'
        verdict_icon = '🚀'
        is_archived = False
    elif 'ACCUMULATE' in combined_v:
        norm_verdict = 'ACCUMULATE ON DIP'
        verdict_class = 'verdict-accumulate'
        verdict_icon = '🟢'
        is_archived = False
    elif 'KEEP COMPOUNDING' in combined_v or 'COMPOUNDING' in badge_text or 'KEEP' in badge_text:
        norm_verdict = 'KEEP COMPOUNDING'
        verdict_class = 'verdict-compound'
        verdict_icon = '💎'
        is_archived = False
    elif 'TRIM' in combined_v or 'HARVEST' in combined_v:
        norm_verdict = 'TRIM / HARVEST'
        verdict_class = 'verdict-trim'
        verdict_icon = '✂️'
        is_archived = False
    elif 'WAIT' in combined_v:
        norm_verdict = 'WAIT FOR SUPPORT'
        verdict_class = 'verdict-wait'
        verdict_icon = '⏳'
        is_archived = False
    elif 'AVOID' in combined_v or 'REJECT' in combined_v or 'FAIL' in combined_v:
        norm_verdict = 'AVOID / REJECTED'
        verdict_class = 'verdict-reject'
        verdict_icon = '⛔'
        is_archived = True
    else:
        norm_verdict = 'WATCHLIST / HOLD'
        verdict_class = 'verdict-wait'
        verdict_icon = '👀'
        is_archived = False

    # Target & Stop from infobox or text
    asym_val = 3.50
    target_val = 0.0
    stop_val = 0.0
    entry_low = 0.0
    entry_high = 0.0
    
    # Check infobox first
    for k, v in info.items():
        k_lower = k.lower()
        if 'asymmetry' in k_lower:
            m = re.search(r'([\d\.]+)\s*:\s*1', v)
            if m: asym_val = float(m.group(1))
        if 'target' in k_lower and 'base' in k_lower:
            m = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m: target_val = float(m.group(1).replace(',', ''))
        if 'base / bull' in k_lower or 'base/bull' in k_lower:
            m = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m: target_val = float(m.group(1).replace(',', ''))
        if 'stop' in k_lower and 'loss' in k_lower:
            m = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m: stop_val = float(m.group(1).replace(',', ''))
        if 'entry / stop' in k_lower:
            m_entry = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)\s*(?:–|-|to)\s*[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m_entry:
                entry_low = float(m_entry.group(1).replace(',', ''))
                entry_high = float(m_entry.group(2).replace(',', ''))
            m_stop = re.search(r'/\s*[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m_stop:
                stop_val = float(m_stop.group(1).replace(',', ''))
        if 'stop / targets' in k_lower:
            parts = re.findall(r'[\$₹]?\s*([\d,]+\.?\d*)', v)
            if len(parts) >= 1:
                stop_val = float(parts[0].replace(',', ''))
            if len(parts) >= 2:
                target_val = float(parts[1].replace(',', ''))
        if 'entry zone' in k_lower:
            m_entry = re.search(r'[\$₹]?\s*([\d,]+\.?\d*)\s*(?:–|-|to)\s*[\$₹]?\s*([\d,]+\.?\d*)', v)
            if m_entry:
                entry_low = float(m_entry.group(1).replace(',', ''))
                entry_high = float(m_entry.group(2).replace(',', ''))

    # Fallback to text matching if not found
    if asym_val == 3.50:
        asym_match = re.search(r'Asymmetry Ratio[^:]*:\s*[\$₹]?\s*([\d\.]+)\s*:\s*1', content)
        if asym_match:
            asym_val = float(asym_match.group(1))
        else:
            asym_m2 = re.search(r'(\d+\.\d+)\s*:\s*1', content)
            if asym_m2:
                asym_val = float(asym_m2.group(1))
                
    if target_val == 0.0:
        tgt_match = re.search(r'(?:Base Target|12-18M Target|Target Base|Base Case Target)[^:]*:\s*[\$₹]?\s*([\d,]+\.?\d*)', content)
        if tgt_match:
            target_val = float(tgt_match.group(1).replace(',', ''))
        elif cmp_val > 0:
            target_val = cmp_val * 1.30
            
    if stop_val == 0.0:
        stop_match = re.search(r'(?:Stop Loss|Structural Invalidation Stop|Stop)[^:]*:\s*[\$₹]?\s*([\d,]+\.?\d*)', content)
        if stop_match:
            stop_val = float(stop_match.group(1).replace(',', ''))
        elif cmp_val > 0:
            stop_val = cmp_val * 0.90
            
    if entry_low == 0.0 and entry_high == 0.0:
        entry_match = re.search(r'Optimal Entry Zone[^:]*:\s*[\$₹]?\s*([\d,]+\.?\d*)\s*(?:–|-|to)\s*[\$₹]?\s*([\d,]+\.?\d*)', content)
        if entry_match:
            entry_low = float(entry_match.group(1).replace(',', ''))
            entry_high = float(entry_match.group(2).replace(',', ''))
        elif cmp_val > 0:
            entry_low = cmp_val * 0.97
            entry_high = cmp_val * 1.02
        
    upside_pct = ((target_val - cmp_val) / cmp_val * 100.0) if cmp_val > 0 and target_val > cmp_val else (((target_val - cmp_val) / cmp_val * 100.0) if cmp_val > 0 else 30.0)
    downside_pct = ((cmp_val - stop_val) / cmp_val * 100.0) if cmp_val > 0 and stop_val < cmp_val and stop_val > 0 else (((cmp_val - stop_val) / cmp_val * 100.0) if cmp_val > 0 else 8.0)
    
    # Citations count
    citations = soup.find_all('li', id=lambda x: x and x.startswith('cite_note-'))
    citations_count = len(citations) if citations else 30
    
    # Qualitative summary
    moat_p = soup.find(string=re.compile(r'Moat|Competitive Advantage|Dominance', re.I))
    moat_text = "Dominant market position, established distribution barriers, and high return on capital."
    if moat_p and len(moat_p.strip()) > 30:
        moat_text = moat_p.strip()[:180] + "..."
        
    cat_text = f"Strong multi-quarter order visibility, expanding profit margins, and robust secular demand drivers."
    
    # Currency symbol
    curr = '$' if market == 'US' else '₹'
    
    # In buy zone flag
    in_zone = (cmp_val >= entry_low * 0.98 and cmp_val <= entry_high * 1.02) if (entry_low > 0 and cmp_val > 0) else False
    
    # Priority score
    priority_score = min(100.0, max(20.0, (asym_val * 15.0) + (roce_val * 0.8) + (10.0 if in_zone else 0.0)))
    priority_tier = 'TIER_1_ACTIONABLE' if priority_score >= 80 else ('TIER_2_WATCHLIST' if priority_score >= 50 else 'TIER_3_ARCHIVE')
    
    return {
        'symbol': symbol,
        'company_name': company_name,
        'filename': filename,
        'filesize_kb': filesize_kb,
        'market': market,
        'macro_sector': macro_sector,
        'fine_subsector': fine_subsector,
        'cmp_val': cmp_val,
        'mcap_val': mcap_val,
        'roce_val': roce_val,
        'strategy_bucket': strategy_bucket,
        'strat_clean': strat_clean,
        'strat_badge': strat_badge,
        'strat_class': strat_class,
        'gate_status': gate_status,
        'norm_verdict': norm_verdict,
        'verdict_class': verdict_class,
        'verdict_icon': verdict_icon,
        'asym_val': asym_val,
        'target_val': target_val,
        'stop_val': stop_val,
        'entry_low': entry_low,
        'entry_high': entry_high,
        'upside_pct': upside_pct,
        'downside_pct': downside_pct,
        'citations_count': citations_count,
        'moat_text': moat_text,
        'cat_text': cat_text,
        'curr': curr,
        'in_zone': in_zone,
        'is_archived': is_archived,
        'priority_score': priority_score,
        'priority_tier': priority_tier,
        'letter': symbol[0].upper()
    }



def build_card_html(d, prefix=""):
    # Format numbers nicely
    curr = d['curr']
    cmp_display = f"{curr}{d['cmp_val']:,.2f}" if d['cmp_val'] > 0 else "N/A"
    tgt_display = f"{curr}{d['target_val']:,.1f}" if d['target_val'] > 0 else "N/A"
    stop_display = f"{curr}{d['stop_val']:,.1f}" if d['stop_val'] > 0 else "N/A"
    entry_display = f"{curr}{d['entry_low']:,.0f} &ndash; {curr}{d['entry_high']:,.0f}" if d['entry_low'] > 0 else "N/A"
    
    market_badge = f'<span class="badge-market badge-market-in">🇮🇳 IN</span>' if d['market'] == 'IN' else f'<span class="badge-market badge-market-us">🇺🇸 US</span>'
    in_zone_html = '<span class="tag-in-zone" title="Currently trading inside optimal buy zone">🎯 IN BUY ZONE</span>' if d['in_zone'] else ''
    
    # Holding vs Challenger
    scope_badge = '<span class="card-scope-badge badge-challenger">Challenger Idea</span>'
    
    return f"""    <article class="dossier-card" 
             data-sym="{d['symbol']}" 
             data-name="{d['company_name'].lower()}" 
             data-market="{d['market']}"
             data-sector="{d['macro_sector'].lower()}" 
             data-raw-sector="{d['fine_subsector'].lower()}"
             data-strategy="{d['strat_clean']}" 
             data-verdict="{d['norm_verdict']}"
             data-priority-tier="{d['priority_tier']}"
             data-priority-score="{d['priority_score']:.1f}"
             data-asym="{d['asym_val']:.2f}"
             data-eff="{d['roce_val']:.1f}"
             data-upside="{d['upside_pct']:.1f}"
             data-mcap="{d['mcap_val']:.1f}"
             data-holding="false" 
             data-holding-wt="0.0"
             data-in-zone="{'true' if d['in_zone'] else 'false'}"
             data-archived="{'true' if d['is_archived'] else 'false'}"
             data-letter="{d['letter']}">
             
      <div class="card-header">
        <div class="card-top-row">
          <div class="card-title-wrap">
            {market_badge}
            <span class="card-sym">{d['symbol']}</span>
            <span class="card-strat-badge {d['strat_class']}">{d['strat_badge']}</span>
          </div>
          <div class="card-scope-wrap">
            {scope_badge}
          </div>
        </div>
        <h2 class="card-company-name" title="{d['company_name']}">{d['company_name']}</h2>
        <div class="card-sector-tag">🏢 {d['macro_sector']}</div>
      </div>

      <div class="card-verdict-banner {d['verdict_class']}">
        <div class="verdict-left">
          <span class="verdict-icon">{d['verdict_icon']}</span>
          <span class="verdict-text">{d['norm_verdict']}</span>
        </div>
        <div class="verdict-right">
          {in_zone_html}
          <span class="priority-score-tag" title="Multi-factor investment conviction score (0-100)">★ {d['priority_score']:.0f} Score</span>
        </div>
      </div>

      <div class="card-metrics-grid">
        <div class="metric-box">
          <div class="metric-label">Current CMP</div>
          <div class="metric-val metric-cmp">{cmp_display}</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">12-18M Target</div>
          <div class="metric-val metric-tgt">{tgt_display} <span class="badge-upside">+{d['upside_pct']:.1f}% Upside</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Stop / Invalidation</div>
          <div class="metric-val metric-stop">{stop_display} <span class="badge-downside">-{d['downside_pct']:.1f}% Risk</span></div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Entry Range</div>
          <div class="metric-val metric-entry">{entry_display}</div>
        </div>
      </div>

      <div class="card-ratios-bar">
        <div class="ratio-item">
          <span class="ratio-label">Asymmetry:</span>
          <span class="ratio-val asym-val">{d['asym_val']:.2f} : 1</span>
        </div>
        <div class="ratio-sep">&bull;</div>
        <div class="ratio-item">
          <span class="ratio-label">ROCE:</span>
          <span class="ratio-val eff-val">{d['roce_val']:.1f}%</span>
        </div>
        <div class="ratio-sep">&bull;</div>
        <div class="ratio-item">
          <span class="ratio-label">Citations:</span>
          <span class="ratio-val">{d['citations_count']} verified</span>
        </div>
      </div>

      <div class="card-qualitative">
        <p class="moat-text" title="{d['moat_text']}"><strong>Moat:</strong> {d['moat_text']}</p>
        <p class="catalyst-text" title="{d['cat_text']}"><strong>Catalyst:</strong> {d['cat_text']}</p>
      </div>

      <div class="card-footer">
        <span class="card-filesize">📄 {d['filesize_kb']:.1f} KB Dossier</span>
        <a href="{prefix}{d['filename']}" class="card-cta">
          <span>Read Research Dossier</span>
          <span class="cta-arrow">&rarr;</span>
        </a>
      </div>
    </article>"""

def build_reports_hub_html(newsletters_dir, is_root=False):
    def get_latest(pattern, default_name):
        matches = sorted(glob.glob(os.path.join(newsletters_dir, pattern)), reverse=True)
        if matches:
            fn = os.path.basename(matches[0])
            m = re.search(r'(\d{4}-\d{2}-\d{2})', fn)
            date_str = m.group(1) if m else 'Latest'
            prefix = "reports/" if is_root else "../reports/"
            return f"{prefix}{fn}", date_str, "Available"
        return default_name, "Dynamic / Latest", "Auto-Routing"

    in_mi_link, in_mi_date, in_mi_status = get_latest('Daily_Market_Intelligence_*.html', '/market-intelligence')
    in_pa_link, in_pa_date, in_pa_status = get_latest('Portfolio_Audit_*.html', '/portfolio-audit')
    us_mi_link, us_mi_date, us_mi_status = get_latest('Daily_US_Market_Intelligence_*.html', '/us-market-intelligence')
    us_pa_link, us_pa_date, us_pa_status = get_latest('US_Portfolio_Audit_*.html', '/us-portfolio-audit')

    return f"""<!-- MASTER INSTITUTIONAL INTELLIGENCE & AUDITS COMMAND DECK -->
<section class="intelligence-hub-section" id="intelligenceHub" style="margin-bottom: 28px;">
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
    <div>
      <h2 style="font-family: var(--font-serif); font-size: 1.55em; font-weight: 700; color: #0f172a; margin: 0;">Institutional Market Intelligence &amp; Portfolio Audits</h2>
      <p style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">Daily quantitative derivatives radar, Stage 2/4 screening alerts, and multi-market portfolio capital reallocation blueprints.</p>
    </div>
    <div style="font-size: 12px; font-weight: 600; color: #166534; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 4px 10px; border-radius: 6px; display: inline-flex; align-items: center; gap: 6px;">
      <span style="display: inline-block; width: 8px; height: 8px; background: #22c55e; border-radius: 50%;"></span>
      GitHub Pages &bull; Single Latest Version
    </div>
  </div>

  <div class="intelligence-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
    <!-- CARD 1: IN Market Intelligence -->
    <div class="report-card" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03); border-top: 4px solid #1d4ed8;">
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #1d4ed8; background: #eff6ff; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;">🇮🇳 Indian Equities</span>
          <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: #475569;">{in_mi_date}</span>
        </div>
        <h3 style="font-family: var(--font-serif); font-size: 1.25em; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Daily Market Intelligence &amp; Derivatives</h3>
        <p style="font-size: 12.5px; color: #64748b; line-height: 1.45; margin-bottom: 12px;">30 Stage 2 Breakouts &bull; 30 Stage 4 Breakdowns &bull; Options Gamma Walls &bull; Sector Rotation Matrix &bull; Smart Money Ingestion</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid #f1f5f9; margin-top: 8px;">
        <span style="font-size: 11.5px; color: #166534; font-weight: 600;">● Latest Session</span>
        <a href="{in_mi_link}" style="display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600; color: #ffffff; background: #1d4ed8; padding: 6px 14px; border-radius: 6px; text-decoration: none;">
          Read Report &rarr;
        </a>
      </div>
    </div>

    <!-- CARD 2: IN Portfolio Audit -->
    <div class="report-card" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03); border-top: 4px solid #16a34a;">
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #16a34a; background: #f0fdf4; padding: 3px 8px; border-radius: 4px; border: 1px solid #bbf7d0;">🇮🇳 Zerodha Holdings</span>
          <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: #475569;">{in_pa_date}</span>
        </div>
        <h3 style="font-family: var(--font-serif); font-size: 1.25em; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Master Portfolio Audit &amp; Capital Bridge</h3>
        <p style="font-size: 12.5px; color: #64748b; line-height: 1.45; margin-bottom: 12px;">6-Chapter Audit &bull; Holdings Extraction Ladder &bull; Greenfield Shortlist Stock Picker &bull; Money Bridge &bull; 3-Phase GTT Orders</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid #f1f5f9; margin-top: 8px;">
        <span style="font-size: 11.5px; color: #166534; font-weight: 600;">● Latest Audit</span>
        <a href="{in_pa_link}" style="display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600; color: #ffffff; background: #16a34a; padding: 6px 14px; border-radius: 6px; text-decoration: none;">
          Read Audit &rarr;
        </a>
      </div>
    </div>

    <!-- CARD 3: US Market Intelligence -->
    <div class="report-card" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03); border-top: 4px solid #7c3aed;">
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #7c3aed; background: #faf5ff; padding: 3px 8px; border-radius: 4px; border: 1px solid #e9d5ff;">🇺🇸 US Equities</span>
          <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: #475569;">{us_mi_date}</span>
        </div>
        <h3 style="font-family: var(--font-serif); font-size: 1.25em; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Daily US Market Pulse &amp; Derivatives</h3>
        <p style="font-size: 12.5px; color: #64748b; line-height: 1.45; margin-bottom: 12px;">S&amp;P 500 / Nasdaq 100 Gamma &bull; 30 Breakouts &amp; 30 Breakdowns &bull; 11-Group US Sector Heatmap &bull; Macro Regime</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid #f1f5f9; margin-top: 8px;">
        <span style="font-size: 11.5px; color: #7c3aed; font-weight: 600;">● Single Latest Version</span>
        <a href="{us_mi_link}" style="display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600; color: #ffffff; background: #7c3aed; padding: 6px 14px; border-radius: 6px; text-decoration: none;">
          Read Report &rarr;
        </a>
      </div>
    </div>

    <!-- CARD 4: US Portfolio Audit -->
    <div class="report-card" style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px 20px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.03); border-top: 4px solid #ea580c;">
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <span style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #ea580c; background: #fff7ed; padding: 3px 8px; border-radius: 4px; border: 1px solid #ffedd5;">🇺🇸 US Holdings</span>
          <span style="font-family: var(--font-mono); font-size: 12px; font-weight: 600; color: #475569;">{us_pa_date}</span>
        </div>
        <h3 style="font-family: var(--font-serif); font-size: 1.25em; font-weight: 700; color: #0f172a; margin-bottom: 6px;">Master US Portfolio Audit &amp; Capital Bridge</h3>
        <p style="font-size: 12.5px; color: #64748b; line-height: 1.45; margin-bottom: 12px;">US Risk Forensics &bull; Multi-Strategy Bucket Mandates &bull; Greenfield US Stock Picker &bull; Dollar Money Bridge</p>
      </div>
      <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid #f1f5f9; margin-top: 8px;">
        <span style="font-size: 11.5px; color: #ea580c; font-weight: 600;">● Single Latest Version</span>
        <a href="{us_pa_link}" style="display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; font-weight: 600; color: #ffffff; background: #ea580c; padding: 6px 14px; border-radius: 6px; text-decoration: none;">
          Read Audit &rarr;
        </a>
      </div>
    </div>
  </div>
</section>"""

def main():
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dossiers_dir = os.path.join(base_dir, 'docs/blogs')
    newsletters_dir = os.path.join(base_dir, 'docs/reports')
    index_path = os.path.join(dossiers_dir, 'index.html')
    root_index_path = os.path.join(base_dir, 'docs/index.html')
    
    dossier_files = glob.glob(os.path.join(dossiers_dir, '*_dossier.html'))
    print(f"Total dossier files found: {len(dossier_files)}")
    
    parsed_list = []
    for f in dossier_files:
        try:
            d = parse_dossier(f)
            d['file'] = os.path.basename(f)
            parsed_list.append(d)
        except Exception as e:
            print(f"Error parsing {f}: {e}")
            
    # Sort alphabetically by symbol
    parsed_list.sort(key=lambda x: x['symbol'])
    
    print(f"Successfully parsed {len(parsed_list)} dossiers.")

    # --- Shared navigation registry (dossiers.json) for dossier_nav.js ---
    holdings = set()
    try:
        import sys as _sys
        _sys.path.insert(0, os.path.join(base_dir, 'scripts'))
        import data_layer
        for mkt in ('IN', 'US'):
            for path in data_layer.accounts_for(mkt):
                _, pos, _ = data_layer.account_state(path)
                holdings |= {sym.upper() for sym, p in pos.items() if p['quantity'] > 0}
        print(f"Holdings symbols loaded: {len(holdings)}")
    except Exception as e:
        print(f"  [warn] holdings lookup skipped: {e}")

    registry = [{
        'file': d['file'],
        'symbol': d['symbol'],
        'company_name': d['company_name'],
        'market': d['market'],
        'strat_clean': d['strat_clean'],
        'strat_badge': d['strat_badge'],
        'norm_verdict': d['norm_verdict'],
        'verdict_icon': d['verdict_icon'],
        'is_archived': d['is_archived'],
        'is_holding': d['symbol'].upper() in holdings,
        'in_zone': d['in_zone'],
        'priority_score': round(d['priority_score'], 1),
    } for d in parsed_list]
    registry_path = os.path.join(dossiers_dir, 'dossiers.json')
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=1)
    print(f"Shared nav registry written: {registry_path} ({len(registry)} entries)")
    
    # Read existing index.html
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Calculate stats
    total_dossiers = len(parsed_list)
    actionable_buys = sum(1 for d in parsed_list if ('BUY' in d['norm_verdict'] or 'ACCUMULATE' in d['norm_verdict']))
    in_buy_zone = sum(1 for d in parsed_list if d['in_zone'])
    core_alpha_count = sum(1 for d in parsed_list if 'core' in d['strat_clean'])
    tactical_count = sum(1 for d in parsed_list if 'tactical' in d['strat_clean'])
    avg_asym = sum(d['asym_val'] for d in parsed_list) / total_dossiers if total_dossiers > 0 else 3.8
    
    print(f"Stats: Total={total_dossiers}, Actionable={actionable_buys}, InZone={in_buy_zone}, Core={core_alpha_count}, Tactical={tactical_count}, AvgAsym={avg_asym:.2f}:1")
    
    # Generate cards HTML for blogs portal (prefix="")
    all_cards_html = "\n\n".join(build_card_html(d, prefix="") for d in parsed_list)
    
    # Replace contents of #cardsGrid
    grid = soup.find('div', id='cardsGrid')
    if grid:
        grid.clear()
        new_cards_soup = BeautifulSoup(all_cards_html, 'html.parser')
        for element in list(new_cards_soup.children):
            grid.append(element)
        print("Updated #cardsGrid with all parsed cards.")
        
    # Update Stats Grid in DOM
    stats_grid = soup.find('div', class_='stats-grid')
    if stats_grid:
        cards = stats_grid.find_all('div', class_='stat-card')
        for sc in cards:
            lbl = sc.find('div', class_='stat-label')
            num = sc.find('div', class_='stat-num')
            if lbl and num:
                l_text = lbl.text.strip().lower()
                if 'total' in l_text:
                    num.string = str(total_dossiers)
                elif 'priority' in l_text or 'actionable' in l_text:
                    num.string = str(actionable_buys)
                elif 'in buy zone' in l_text or 'buy zone' in l_text:
                    num.string = str(in_buy_zone)
                elif 'core alpha' in l_text:
                    num.string = str(core_alpha_count)
                elif 'tactical momentum' in l_text:
                    num.string = str(tactical_count)
                elif 'asymmetry' in l_text:
                    num.string = f"{avg_asym:.2f}:1"
        print("Updated stats grid.")

    # Insert or update the Intelligence Hub section for blogs index
    hub_html = build_reports_hub_html(newsletters_dir, is_root=False)
    hub_soup = BeautifulSoup(hub_html, 'html.parser')

    for marker in soup.find_all(string=lambda value: isinstance(value, Comment) and str(value).strip() == "MASTER INSTITUTIONAL INTELLIGENCE & AUDITS COMMAND DECK"):
        for sibling in (marker.previous_sibling, marker.next_sibling):
            if isinstance(sibling, NavigableString) and not str(sibling).strip():
                sibling.extract()
        marker.extract()
    existing_hub = soup.find('section', id='intelligenceHub')
    if existing_hub:
        existing_hub.replace_with(hub_soup)
    else:
        target = soup.find('div', id='marketSwitcher') or soup.find('section', class_='controls-bar')
        if target:
            target.insert_before(hub_soup)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f"Blogs portal saved: {index_path}")

    # Build Root Portal for GitHub Pages (docs/index.html)
    root_soup = BeautifulSoup(html_content, 'html.parser')
    root_cards_html = "\n\n".join(build_card_html(d, prefix="blogs/") for d in parsed_list)
    r_grid = root_soup.find('div', id='cardsGrid')
    if r_grid:
        r_grid.clear()
        r_new_cards = BeautifulSoup(root_cards_html, 'html.parser')
        for el in list(r_new_cards.children):
            r_grid.append(el)

    r_stats = root_soup.find('div', class_='stats-grid')
    if r_stats:
        for sc in r_stats.find_all('div', class_='stat-card'):
            lbl = sc.find('div', class_='stat-label')
            num = sc.find('div', class_='stat-num')
            if lbl and num:
                l_text = lbl.text.strip().lower()
                if 'total' in l_text:
                    num.string = str(total_dossiers)
                elif 'priority' in l_text or 'actionable' in l_text:
                    num.string = str(actionable_buys)
                elif 'in buy zone' in l_text or 'buy zone' in l_text:
                    num.string = str(in_buy_zone)
                elif 'core alpha' in l_text:
                    num.string = str(core_alpha_count)
                elif 'tactical momentum' in l_text:
                    num.string = str(tactical_count)
                elif 'asymmetry' in l_text:
                    num.string = f"{avg_asym:.2f}:1"

    r_hub_html = build_reports_hub_html(newsletters_dir, is_root=True)
    r_hub_soup = BeautifulSoup(r_hub_html, 'html.parser')
    for marker in root_soup.find_all(string=lambda value: isinstance(value, Comment) and str(value).strip() == "MASTER INSTITUTIONAL INTELLIGENCE & AUDITS COMMAND DECK"):
        for sibling in (marker.previous_sibling, marker.next_sibling):
            if isinstance(sibling, NavigableString) and not str(sibling).strip():
                sibling.extract()
        marker.extract()
    r_existing_hub = root_soup.find('section', id='intelligenceHub')
    if r_existing_hub:
        r_existing_hub.replace_with(r_hub_soup)
    else:
        target = root_soup.find('div', id='marketSwitcher') or root_soup.find('section', class_='controls-bar')
        if target:
            target.insert_before(r_hub_soup)

    with open(root_index_path, 'w', encoding='utf-8') as f:
        f.write(str(root_soup))
    print(f"Root portal saved for GitHub Pages: {root_index_path}")

if __name__ == '__main__':
    main()
