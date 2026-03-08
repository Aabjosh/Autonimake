import { useState, useEffect, useRef, useCallback } from "react";

const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Outfit:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
:root{
  --ink:#0b1d3a;--navy:#0f2554;--blue:#1a4fde;--cobalt:#2563eb;
  --sky:#5b8ff8;--frost:#c7d9ff;--cream:#f5f0e8;--parchment:#ede8de;
  --linen:#e6e0d4;--white:#fdfcfa;--muted:#8fa3c0;
  --success:#34d399;--warn:#fb923c;
}
body{font-family:'Outfit',sans-serif;background:#ddd8cf;}

.shell{
  width:390px;height:844px;margin:0 auto;
  position:relative;overflow:hidden;background:var(--cream);
  border-radius:50px;
  box-shadow:0 0 0 1px rgba(0,0,0,0.08),0 60px 160px rgba(11,29,58,0.45),inset 0 1px 0 rgba(255,255,255,0.6);
}

/* SCREEN TRANSITIONS */
.screen{
  position:absolute;inset:0;display:flex;flex-direction:column;
  transform:translateX(100%);opacity:0;pointer-events:none;
  transition:transform 0.48s cubic-bezier(.77,0,.175,1),opacity 0.38s ease;
  will-change:transform;
}
.screen.active{transform:translateX(0);opacity:1;pointer-events:all;}
.screen.exiting{transform:translateX(-60px);opacity:0;pointer-events:none;}

/* ── SPLASH ── */
.splash{background:var(--ink);cursor:pointer;overflow:hidden;}
.grain{position:absolute;inset:0;opacity:.5;pointer-events:none;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.05'/%3E%3C/svg%3E");
}
.glow{position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none;}
.glow-a{width:340px;height:340px;top:-80px;right:-80px;background:radial-gradient(circle,rgba(26,79,222,.55) 0%,transparent 70%);animation:floatA 8s ease-in-out infinite;}
.glow-b{width:260px;height:260px;bottom:40px;left:-40px;background:radial-gradient(circle,rgba(37,99,235,.35) 0%,transparent 70%);animation:floatB 10s ease-in-out infinite;}
.glow-c{width:180px;height:180px;top:48%;left:38%;background:radial-gradient(circle,rgba(91,143,248,.18) 0%,transparent 70%);animation:floatA 6s ease-in-out infinite reverse;}
@keyframes floatA{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(18px,-18px) scale(1.07)}}
@keyframes floatB{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(-14px,14px) scale(1.05)}}

.splash-inner{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:0 36px;text-align:center;}
.s-eye{font-size:10px;letter-spacing:.4em;text-transform:uppercase;color:var(--sky);font-weight:600;margin-bottom:20px;opacity:0;animation:riseIn .7s ease .4s forwards;}
.s-title{font-family:'Instrument Serif',serif;font-size:52px;line-height:1.05;color:var(--white);letter-spacing:-.02em;opacity:0;animation:riseIn .9s cubic-bezier(.22,1,.36,1) .6s forwards;}
.s-title em{font-style:italic;color:var(--sky);}
.s-sub{font-size:13px;font-weight:300;letter-spacing:.06em;color:rgba(245,240,232,.4);margin-top:14px;opacity:0;animation:riseIn .7s ease .9s forwards;}

.swipe-cue{position:absolute;bottom:56px;left:0;right:0;display:flex;flex-direction:column;align-items:center;gap:10px;opacity:0;animation:riseIn .7s ease 1.2s forwards;z-index:2;}
.sw-track{width:56px;height:3px;border-radius:2px;background:rgba(255,255,255,.1);overflow:hidden;}
.sw-bar{height:100%;width:40%;border-radius:2px;background:linear-gradient(90deg,var(--sky),var(--blue));animation:glide 2s ease-in-out infinite 1.8s;}
@keyframes glide{0%{transform:translateX(0);opacity:1}70%{transform:translateX(150%);opacity:1}71%{opacity:0}72%{transform:translateX(-150%)}73%{opacity:1}100%{transform:translateX(0);opacity:1}}
.sw-lbl{font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.28);font-weight:500;}

/* ── SHARED PAGE ── */
.page{background:var(--cream);flex-direction:column;}
.topbar{position:relative;z-index:4;padding:54px 26px 0;flex-shrink:0;}
.step-row{display:flex;gap:5px;margin-bottom:18px;}
.s-dot{height:3px;border-radius:2px;background:var(--linen);flex:1;transition:background .4s,transform .3s;}
.s-dot.done{background:var(--blue);}
.s-dot.now{background:var(--sky);transform:scaleY(1.6);}
.pg-title{font-family:'Instrument Serif',serif;font-size:36px;line-height:1.1;color:var(--ink);letter-spacing:-.02em;}
.pg-title em{font-style:italic;color:var(--blue);}
.pg-sub{font-size:13px;font-weight:400;color:var(--muted);margin-top:6px;line-height:1.5;}
.scroll{flex:1;overflow-y:auto;padding:24px 22px 36px;scrollbar-width:none;}
.scroll::-webkit-scrollbar{display:none;}

/* ── MODE CARDS ── */
.mode-cards{display:flex;flex-direction:column;gap:12px;margin-top:20px;}
.mc{background:var(--white);border:1.5px solid var(--linen);border-radius:22px;padding:20px;display:flex;align-items:center;gap:16px;cursor:pointer;transition:all .3s cubic-bezier(.4,0,.2,1);position:relative;overflow:hidden;-webkit-tap-highlight-color:transparent;}
.mc::before{content:'';position:absolute;inset:0;background:linear-gradient(130deg,var(--navy),var(--blue));opacity:0;transition:opacity .3s;border-radius:inherit;}
.mc.on::before{opacity:1;}
.mc.on{border-color:var(--blue);transform:translateY(-2px);box-shadow:0 14px 40px rgba(26,79,222,.28);}
.mc:not(.on):hover{border-color:var(--frost);transform:translateY(-1px);box-shadow:0 8px 24px rgba(11,29,58,.08);}
.mc-ico{width:54px;height:54px;border-radius:15px;background:var(--cream);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;position:relative;z-index:1;transition:background .3s,transform .3s;}
.mc.on .mc-ico{background:rgba(255,255,255,.13);transform:scale(1.07) rotate(-4deg);}
.mc-txt{position:relative;z-index:1;flex:1;}
.mc-name{font-weight:700;font-size:16px;color:var(--ink);transition:color .3s;}
.mc.on .mc-name{color:var(--white);}
.mc-hint{font-size:12px;color:var(--muted);margin-top:2px;transition:color .3s;line-height:1.4;}
.mc.on .mc-hint{color:rgba(255,255,255,.6);}
.mc-chk{width:24px;height:24px;border-radius:50%;border:1.5px solid var(--linen);display:flex;align-items:center;justify-content:center;font-size:12px;color:transparent;flex-shrink:0;position:relative;z-index:1;transition:all .3s;}
.mc.on .mc-chk{background:rgba(255,255,255,.2);border-color:rgba(255,255,255,.4);color:var(--white);}

/* ── TERMINAL ── */
.term{margin-top:18px;background:var(--ink);border-radius:18px;padding:16px 18px;overflow:hidden;animation:riseIn .45s cubic-bezier(.22,1,.36,1);}
.term-bar{display:flex;gap:6px;margin-bottom:12px;align-items:center;}
.td{width:9px;height:9px;border-radius:50%;}
.tc{background:#ff5f57;}.tm{background:#febc2e;}.tx{background:#28c840;}
.tt{margin-left:8px;font-size:10px;letter-spacing:.1em;color:rgba(255,255,255,.22);text-transform:uppercase;font-weight:500;}
.tl{font-family:'Courier New',monospace;font-size:11.5px;line-height:1.9;color:rgba(255,255,255,.42);}
.tl .p{color:var(--sky);}.tl .ok{color:var(--success);}.tl .wt{color:var(--warn);}.tl .cmd{color:rgba(255,255,255,.85);}
.cur{display:inline-block;width:7px;height:13px;background:var(--sky);margin-left:2px;vertical-align:text-bottom;animation:blink 1.1s step-end infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

/* ── FIELDS ── */
.ey{font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;font-weight:700;color:var(--muted);margin-bottom:7px;margin-top:16px;}
.ey:first-child{margin-top:0;}
.f{background:var(--white);border:1.5px solid var(--linen);border-radius:14px;overflow:hidden;transition:border-color .2s,box-shadow .2s;}
.f:focus-within{border-color:var(--cobalt);box-shadow:0 0 0 4px rgba(37,99,235,.1);}
.f-row{display:flex;align-items:center;}
.f-ico{padding:0 9px 0 15px;font-size:14px;flex-shrink:0;color:var(--muted);}
.f input,.f textarea{flex:1;padding:13px 15px 13px 4px;background:transparent;border:none;outline:none;font-family:'Outfit',sans-serif;font-size:14px;font-weight:400;color:var(--ink);}
.f textarea{resize:none;height:72px;line-height:1.6;padding:12px 15px;}
.f input::placeholder,.f textarea::placeholder{color:var(--muted);}

/* upload zone */
.upz{background:var(--white);border:1.5px dashed var(--linen);border-radius:14px;padding:18px;display:flex;align-items:center;gap:13px;cursor:pointer;transition:all .25s;position:relative;overflow:hidden;}
.upz:hover,.upz.drag{border-color:var(--cobalt);background:rgba(37,99,235,.03);box-shadow:0 0 0 4px rgba(37,99,235,.08);}
.upz.got{border-style:solid;border-color:var(--cobalt);background:rgba(37,99,235,.04);}
.up-ico{width:40px;height:40px;border-radius:12px;background:var(--cream);display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;transition:transform .25s;}
.upz:hover .up-ico{transform:scale(1.1) translateY(-2px);}
.up-title{font-size:13px;font-weight:600;color:var(--ink);}
.up-sub{font-size:11px;color:var(--muted);margin-top:2px;}
.up-input{position:absolute;inset:0;opacity:0;cursor:pointer;}
.opt{display:inline-block;font-size:9px;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:var(--muted);background:var(--parchment);border-radius:20px;padding:2px 8px;margin-left:7px;vertical-align:middle;}

/* trigger card */
.tc-card{background:var(--white);border:1.5px solid var(--linen);border-radius:20px;padding:18px;margin-bottom:12px;animation:slideUp .38s cubic-bezier(.22,1,.36,1) both;}
@keyframes slideUp{from{opacity:0;transform:translateY(14px) scale(.98)}to{opacity:1;transform:none}}
.tc-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.tc-num{display:flex;align-items:center;gap:8px;}
.tc-badge{width:26px;height:26px;border-radius:8px;background:linear-gradient(135deg,var(--blue),var(--cobalt));color:white;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;}
.tc-lbl{font-size:12px;font-weight:600;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;}
.x-btn{width:30px;height:30px;border-radius:50%;border:none;background:var(--cream);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:13px;color:var(--muted);transition:all .2s;-webkit-tap-highlight-color:transparent;}
.x-btn:hover{background:#fee2e2;color:#dc2626;}

/* ── BUTTONS ── */
.btn{width:100%;padding:15px 20px;border-radius:15px;border:none;cursor:pointer;font-family:'Outfit',sans-serif;font-weight:700;font-size:14px;letter-spacing:.02em;display:flex;align-items:center;justify-content:center;gap:8px;transition:all .22s cubic-bezier(.4,0,.2,1);-webkit-tap-highlight-color:transparent;outline:none;}
.btn:active{transform:scale(.97);}
.btn-p{background:linear-gradient(135deg,var(--navy) 0%,var(--blue) 55%,var(--cobalt) 100%);color:white;box-shadow:0 6px 24px rgba(26,79,222,.32);}
.btn-p:hover{box-shadow:0 10px 32px rgba(26,79,222,.42);transform:translateY(-1px);}
.btn-g{background:var(--white);color:var(--blue);border:1.5px solid var(--linen);}
.btn-g:hover{border-color:var(--cobalt);background:rgba(37,99,235,.04);}
.btn-d{background:var(--white);color:#dc2626;border:1.5px solid #fecaca;}
.btn-d:hover{background:#fef2f2;border-color:#dc2626;}
.r2{display:flex;gap:10px;margin-top:10px;}.r2 .btn{flex:1;}
.mt{margin-top:12px;}
.back-btn{background:none;border:none;cursor:pointer;color:var(--muted);font-family:'Outfit',sans-serif;font-size:13px;font-weight:500;padding:4px 0;margin-bottom:14px;display:flex;align-items:center;gap:5px;transition:color .2s;-webkit-tap-highlight-color:transparent;}
.back-btn:hover{color:var(--blue);}

/* ══ LIVE SCREEN ══ */
.live-s{background:#090f1e;}
.live-top{padding:54px 26px 18px;flex-shrink:0;}
.l-eye{font-size:10px;letter-spacing:.35em;text-transform:uppercase;color:rgba(91,143,248,.55);font-weight:600;margin-bottom:8px;}
.l-title{font-family:'Instrument Serif',serif;font-size:32px;color:white;letter-spacing:-.02em;line-height:1.1;}
.l-title em{font-style:italic;color:var(--sky);}
.status-bar{display:flex;align-items:center;gap:8px;margin-top:13px;}
.s-led{width:7px;height:7px;border-radius:50%;background:var(--success);box-shadow:0 0 8px var(--success);animation:pulseLed 2s ease-in-out infinite;}
@keyframes pulseLed{0%,100%{box-shadow:0 0 6px var(--success)}50%{box-shadow:0 0 14px var(--success)}}
.s-txt{font-size:11.5px;font-weight:500;color:rgba(255,255,255,.42);letter-spacing:.04em;}

.cam-wrap{margin:0 22px;flex-shrink:0;}
.cam-box{background:#0d1829;border:1px solid rgba(91,143,248,.18);border-radius:22px;height:218px;display:flex;flex-direction:column;align-items:center;justify-content:center;position:relative;overflow:hidden;}
.corners{position:absolute;inset:10px;pointer-events:none;}
.cr{position:absolute;width:18px;height:18px;border-color:rgba(91,143,248,.5);border-style:solid;border-width:0;}
.cr-tl{top:0;left:0;border-top-width:2px;border-left-width:2px;border-radius:4px 0 0 0;}
.cr-tr{top:0;right:0;border-top-width:2px;border-right-width:2px;border-radius:0 4px 0 0;}
.cr-bl{bottom:0;left:0;border-bottom-width:2px;border-left-width:2px;border-radius:0 0 0 4px;}
.cr-br{bottom:0;right:0;border-bottom-width:2px;border-right-width:2px;border-radius:0 0 4px 0;}
.scan{position:absolute;left:0;right:0;height:1.5px;background:linear-gradient(90deg,transparent,rgba(91,143,248,.7) 30%,rgba(91,143,248,.9) 50%,rgba(91,143,248,.7) 70%,transparent);animation:scanMove 2.8s linear infinite;}
@keyframes scanMove{0%{top:10%;opacity:0}8%{opacity:1}92%{opacity:1}100%{top:90%;opacity:0}}
.cam-ico{font-size:36px;opacity:.18;}
.cam-lbl{font-size:12px;color:rgba(91,143,248,.38);margin-top:6px;letter-spacing:.08em;}
.fire-flash{position:absolute;inset:0;background:rgba(52,211,153,.15);border-radius:inherit;opacity:0;pointer-events:none;animation:flash .7s ease forwards;}
@keyframes flash{0%{opacity:1}100%{opacity:0}}

.live-body{flex:1;overflow-y:auto;padding:16px 22px 28px;scrollbar-width:none;}
.live-body::-webkit-scrollbar{display:none;}
.pl-lbl{font-size:9.5px;letter-spacing:.3em;text-transform:uppercase;font-weight:700;color:rgba(143,163,192,.5);margin-bottom:10px;}

.pill{background:rgba(255,255,255,.04);border:1px solid rgba(91,143,248,.13);border-radius:16px;padding:13px 15px;display:flex;align-items:center;gap:12px;margin-bottom:9px;transition:all .2s;cursor:pointer;position:relative;overflow:hidden;-webkit-tap-highlight-color:transparent;}
.pill::before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(52,211,153,.08),transparent);opacity:0;transition:opacity .2s;}
.pill.hot::before{opacity:1;}
.pill:active{transform:scale(.99);}
.p-ico{width:38px;height:38px;border-radius:11px;background:rgba(91,143,248,.1);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;transition:transform .2s;}
.pill.hot .p-ico{transform:scale(1.14);}
.p-info{flex:1;}
.p-name{font-size:14px;font-weight:700;color:rgba(255,255,255,.9);}
.p-cmt{font-size:11px;color:rgba(143,163,192,.65);margin-top:2px;font-style:italic;}
.p-test{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:rgba(91,143,248,.6);padding:5px 10px;border-radius:8px;border:1px solid rgba(91,143,248,.2);background:rgba(91,143,248,.07);transition:all .2s;flex-shrink:0;}
.pill.hot .p-test{color:var(--success);border-color:rgba(52,211,153,.4);background:rgba(52,211,153,.08);}

.toast{position:absolute;top:58px;left:50%;transform:translateX(-50%) translateY(0);background:var(--ink);color:white;padding:9px 18px;border-radius:30px;font-size:12px;font-weight:600;letter-spacing:.04em;white-space:nowrap;border:1px solid rgba(52,211,153,.3);box-shadow:0 8px 24px rgba(0,0,0,.35);z-index:100;animation:toastIn .35s cubic-bezier(.22,1,.36,1) forwards,toastOut .3s ease 1.8s forwards;}
@keyframes toastIn{from{opacity:0;transform:translateX(-50%) translateY(-18px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
@keyframes toastOut{to{opacity:0;transform:translateX(-50%) translateY(-10px)}}

.back-btn-live{background:none;border:none;cursor:pointer;color:rgba(91,143,248,.42);font-family:'Outfit',sans-serif;font-size:13px;font-weight:500;padding:4px 0;margin-bottom:14px;display:flex;align-items:center;gap:5px;transition:color .2s;-webkit-tap-highlight-color:transparent;}
.back-btn-live:hover{color:var(--sky);}

@keyframes riseIn{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
`;

const mk = () => ({ id: crypto.randomUUID(), name: "", comment: "", video: "", file: "" });

export default function AutoniMAKE() {
  const [screen, setScreen]       = useState("splash");
  const [prev,   setPrev]         = useState(null);
  const [mode,   setMode]         = useState(null);
  const [trigs,  setTrigs]        = useState([mk()]);
  const [lines,  setLines]        = useState(0);
  const [toast,  setToast]        = useState(null);
  const [firing, setFiring]       = useState(null);
  const [camFlash, setCamFlash]   = useState(false);
  const toastRef = useRef(null);
  const tx = useRef(null);

  const go = useCallback(next => { setPrev(screen); setScreen(next); }, [screen]);

  useEffect(() => {
    if (!mode) return;
    setLines(0);
    const ts = [
      setTimeout(() => setLines(1), 100),
      setTimeout(() => setLines(2), 600),
      setTimeout(() => setLines(3), 1100),
      setTimeout(() => setLines(4), 1750),
    ];
    return () => ts.forEach(clearTimeout);
  }, [mode]);

  const addTrig  = ()       => setTrigs(t => [...t, mk()]);
  const rmTrig   = id       => setTrigs(t => t.length > 1 ? t.filter(x => x.id !== id) : t);
  const upd      = (id,k,v) => setTrigs(t => t.map(x => x.id === id ? {...x,[k]:v} : x));

  const fire = t => {
    if (firing) return;
    setFiring(t.id); setCamFlash(true);
    clearTimeout(toastRef.current);
    setToast(`✓ "${t.name || "trigger"}" executed`);
    toastRef.current = setTimeout(() => setToast(null), 2300);
    setTimeout(() => setFiring(null), 950);
    setTimeout(() => setCamFlash(false), 750);
  };

  const named = trigs.filter(t => t.name.trim());

  const cls = s => `screen${screen===s?" active":prev===s&&screen!==s?" exiting":""}`;

  return (
    <>
      <style>{CSS}</style>
      <div className="shell">

        {/* SPLASH */}
        <div className={cls("splash")+" splash"}
          onClick={() => go("personalize")}
          onTouchStart={e => tx.current = e.touches[0].clientX}
          onTouchEnd={e => { if (tx.current - e.changedTouches[0].clientX > 40) go("personalize"); }}
        >
          <div className="grain"/>
          <div className="glow glow-a"/><div className="glow glow-b"/><div className="glow glow-c"/>
          <div className="splash-inner">
            <div className="s-eye">Gesture Intelligence Platform</div>
            <div className="s-title">Welcome to<br/><em>AutoniMAKE</em></div>
            <div className="s-sub">Train. Trigger. Control. Anything.</div>
          </div>
          <div className="swipe-cue">
            <div className="sw-track"><div className="sw-bar"/></div>
            <div className="sw-lbl">Swipe or tap to begin</div>
          </div>
        </div>

        {/* PERSONALIZE */}
        <div className={cls("personalize")+" page"}>
          <div className="topbar">
            <button className="back-btn" onClick={() => go("splash")}>← Back</button>
            <div className="step-row">
              <div className="s-dot now"/><div className="s-dot"/>
            </div>
            <div className="pg-title">Personalize your<br/><em>model via:</em></div>
            <div className="pg-sub">Choose how you'll communicate with your machine.</div>
          </div>
          <div className="scroll">
            <div className="mode-cards">
              {[
                {id:"hands", icon:"✋", name:"Hands", hint:"Use gestures & signs as live triggers", file:"hands_recognition.py"},
                {id:"object", icon:"🎯", name:"Custom Object", hint:"Train any physical object as a controller", file:"object_recognition.py"},
              ].map(m => (
                <div key={m.id} className={`mc${mode===m.id?" on":""}`} onClick={() => setMode(m.id)}>
                  <div className="mc-ico">{m.icon}</div>
                  <div className="mc-txt">
                    <div className="mc-name">{m.name}</div>
                    <div className="mc-hint">{m.hint}</div>
                  </div>
                  <div className="mc-chk">{mode===m.id?"✓":""}</div>
                </div>
              ))}
            </div>

            {mode && (<>
              <div className="term">
                <div className="term-bar">
                  <div className="td tc"/><div className="td tm"/><div className="td tx"/>
                  <div className="tt">AutoniMAKE Runtime</div>
                </div>
                {lines>=1 && <div className="tl"><span className="p">$</span> <span className="cmd">python {mode==="hands"?"hands_recognition.py":"object_recognition.py"}</span></div>}
                {lines>=2 && <div className="tl"><span className="ok">✓</span> PyTorch model loaded</div>}
                {lines>=3 && <div className="tl"><span className="ok">✓</span> Camera stream initialized</div>}
                {lines>=4
                  ? <div className="tl"><span className="wt">⏳</span> Awaiting training data...</div>
                  : lines>=1 && <div className="tl" style={{opacity:.35}}>...<span className="cur"/></div>
                }
              </div>
              <button className="btn btn-p mt" onClick={() => go("training")}>
                Continue to Training →
              </button>
            </>)}
          </div>
        </div>

        {/* TRAINING */}
        <div className={cls("training")+" page"}>
          <div className="topbar">
            <button className="back-btn" onClick={() => go("personalize")}>← Personalize</button>
            <div className="step-row">
              <div className="s-dot done"/><div className="s-dot now"/>
            </div>
            <div className="pg-title">Configure your<br/><em>triggers</em></div>
            <div className="pg-sub">Each folder name becomes a live trigger for your machine.</div>
          </div>
          <div className="scroll">
            {trigs.map((t,i) => (
              <div className="tc-card" key={t.id}>
                <div className="tc-top">
                  <div className="tc-num">
                    <div className="tc-badge">{i+1}</div>
                    <div className="tc-lbl">Trigger {i+1}</div>
                  </div>
                  {trigs.length > 1 && <button className="x-btn" onClick={() => rmTrig(t.id)}>✕</button>}
                </div>

                <div className="ey">Training Video</div>
                <label className={`upz${t.file?" got":""}`}>
                  <div className="up-ico">{t.file?"🎬":"📂"}</div>
                  <div>
                    <div className="up-title">{t.file||"Upload or drop a video"}</div>
                    <div className="up-sub">{t.file?"Tap to replace":"MP4, MOV, AVI — or paste URL below"}</div>
                  </div>
                  <input type="file" accept="video/*" className="up-input"
                    onChange={e => { const f=e.target.files?.[0]; if(f) upd(t.id,"file",f.name); }}/>
                </label>

                <div className="ey" style={{marginTop:10}}>Or paste a URL</div>
                <div className="f">
                  <div className="f-row">
                    <div className="f-ico">🔗</div>
                    <input type="text" placeholder="https://…" value={t.video} onChange={e=>upd(t.id,"video",e.target.value)}/>
                  </div>
                </div>

                <div className="ey" style={{marginTop:14}}>Trigger Folder Name</div>
                <div className="f">
                  <div className="f-row">
                    <div className="f-ico">📁</div>
                    <input type="text" placeholder="e.g. peace_sign, fist, wave…"
                      value={t.name}
                      onChange={e=>upd(t.id,"name",e.target.value.replace(/\s/g,"_"))}/>
                  </div>
                </div>

                <div className="ey" style={{marginTop:14}}>
                  Debug Comment <span className="opt">Optional</span>
                </div>
                <div className="f">
                  <textarea placeholder="e.g. Peace sign → drive rover forward at 60%…"
                    value={t.comment} onChange={e=>upd(t.id,"comment",e.target.value)}/>
                </div>
              </div>
            ))}

            <button className="btn btn-g" onClick={addTrig}>+ Add Another Trigger</button>
            <div className="r2">
              <button className="btn btn-d"
                onClick={() => { setTrigs([mk()]); setMode(null); go("personalize"); }}>
                ↺ Restart
              </button>
              <button className="btn btn-p" onClick={() => go("live")}>✓ End Training</button>
            </div>
          </div>
        </div>

        {/* LIVE */}
        <div className={cls("live")+" screen live-s"} style={{flexDirection:"column"}}>
          {toast && <div className="toast">{toast}</div>}

          <div className="live-top">
            <button className="back-btn-live" onClick={() => go("training")}>← Training</button>
            <div className="l-eye">AutoniMAKE — Active Session</div>
            <div className="l-title">Model is<br/><em>running</em></div>
            <div className="status-bar">
              <div className="s-led"/>
              <div className="s-txt">
                PyTorch active · {mode==="hands"?"hands_recognition.py":"object_recognition.py"} · {named.length} trigger{named.length!==1?"s":""} loaded
              </div>
            </div>
          </div>

          <div className="cam-wrap">
            <div className="cam-box">
              {camFlash && <div className="fire-flash" key={Date.now()}/>}
              <div className="corners">
                <div className="cr cr-tl"/><div className="cr cr-tr"/>
                <div className="cr cr-bl"/><div className="cr cr-br"/>
              </div>
              <div className="scan"/>
              <div className="cam-ico">📷</div>
              <div className="cam-lbl">Waiting for detection…</div>
            </div>
          </div>

          <div className="live-body">
            <div className="pl-lbl">Trained triggers — tap any to test fire</div>
            {named.length===0 && (
              <div style={{color:"rgba(143,163,192,.4)",fontSize:13,textAlign:"center",padding:"20px 0"}}>
                No named triggers yet. Go back to add folder names.
              </div>
            )}
            {named.map(t => (
              <div key={t.id} className={`pill${firing===t.id?" hot":""}`} onClick={() => fire(t)}>
                <div className="p-ico">{mode==="hands"?"✋":"🎯"}</div>
                <div className="p-info">
                  <div className="p-name">/{t.name}</div>
                  {t.comment && <div className="p-cmt">{t.comment}</div>}
                </div>
                <div className="p-test">{firing===t.id?"Fired ✓":"Test"}</div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </>
  );
}
