from flask import Flask, redirect, render_template_string, request, session, url_for
import random

app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret"

PAGE = r"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>何人正解？</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#19233a;background:#f3f5fa}*{box-sizing:border-box}body{margin:0;padding:24px 14px}.wrap{max-width:680px;margin:auto}.card{background:white;border-radius:18px;padding:26px;margin:16px 0;box-shadow:0 8px 28px #18284a12}h1{font-size:32px;margin:0 0 8px}h2{font-size:22px;margin-top:0}.muted{color:#667085}.badge{display:inline-block;background:#edf2ff;color:#3b55a5;border-radius:999px;padding:6px 12px;font-weight:700}.target{font-size:38px;font-weight:800;color:#5946c7;margin:16px 0}label{display:block;font-weight:650;margin:14px 0 6px}input,textarea{width:100%;padding:12px;border:1px solid #d5dbea;border-radius:10px;font:inherit}textarea{min-height:82px;resize:vertical}button{background:#5747cb;color:white;border:0;border-radius:10px;padding:12px 18px;font:inherit;font-weight:700;cursor:pointer;margin-top:14px}button.secondary{background:#e9ecf5;color:#27314b}button.danger{background:#a43645}.counter{display:flex;align-items:center;gap:20px;margin:8px 0 18px}.counter button{margin:0;background:#2878d0;color:white;font-size:24px;line-height:1;min-width:52px;padding:10px}.counter button.secondary{background:#e9ecf5;color:#27314b}.counter strong{font-size:24px;min-width:24px;text-align:center}.row{display:flex;gap:10px;flex-wrap:wrap}.row button{flex:1}.flash{background:#fff3cf;padding:12px;border-radius:10px;margin:12px 0}.score{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #edf0f5}.answer{padding:12px;border:1px solid #e5e8f0;border-radius:10px;margin:9px 0}.answer label{display:flex;gap:10px;align-items:center;margin:0}.answer input{width:auto}small{color:#667085}
 .name-grid{display:grid;grid-template-columns:1fr 1fr;column-gap:20px;align-items:start}.name-field{width:100%}.name-field input{width:100%}
</style></head><body><main class="wrap"><h1>何人正解？</h1><div class="muted">出題者は目標人数を狙って質問を作ろう。みんなの回答後にお題を公開！</div>
{% if msg %}<div class="flash">{{msg}}</div>{% endif %}
{% if not players %}<section class="card"><h2>ゲームを始める</h2><form method="post" action="/start"><label>参加人数</label><div class="counter"><button id="minusButton" type="button" onclick="changeCount(-1)">−</button><strong id="count">{{count or 3}}</strong><button id="plusButton" type="button" onclick="changeCount(1)">＋</button></div><input type="hidden" name="count" id="countInput" value="{{count or 3}}"><div id="nameFields"></div><button>参加者を登録</button></form></section>
{% else %}<section class="card"><h2>スコア</h2>{% for p in players %}<div class="score"><span>{{p}}</span><strong>{{scores.get(p,0)}} 点</strong></div>{% endfor %}<form method="post" action="/reset"><button class="secondary" type="submit">人数登録に戻る</button></form></section>
{% if phase == 'confirm' %}<section class="card"><span class="badge">ラウンド {{round_no}}</span><h2>出題者の確認</h2><p><strong>{{setter}} さんが出題者です。</strong></p><p>出題者だけ画面を見て、お題を確認してください。準備ができたらボタンを押してください。</p><form method="post" action="/show_prompt"><button>お題を確認する</button></form></section>
{% elif phase == 'setup' %}<section class="card"><span class="badge">ラウンド {{round_no}}</span><h2>お題</h2><p><strong>{{setter}}</strong> さんだけ画面を見てください。</p><div class="target">{{target}}人が正解</div><form method="post" action="/question"><label>質問</label><textarea name="question" required placeholder="みんなが答えられそうな質問を考えよう"></textarea><label>正解（出題者だけが入力）</label><input name="answer" required placeholder="正解を入力"><button>質問を確定して回答へ</button></form></section>
{% elif phase == 'answers' %}<section class="card"><span class="badge">質問</span><h2>{{question}}</h2><p class="muted">回答する人だけ画面を見てください。ほかの人の回答は表示されません。</p><form method="post" action="/submit_answer"><label>{{current_answerer}} さんの回答</label><input name="answer" required autocomplete="off"><button>回答を送信して次の人へ</button></form></section>
{% elif phase == 'mark' %}<section class="card"><span class="badge">回答を判定</span><h2>{{question}}</h2><p>正解は <strong>{{answer}}</strong>。正解した人にチェックしてください。</p><form method="post" action="/reveal">{% for p,a in answers %}<div class="answer"><label><input type="checkbox" name="correct" value="{{loop.index0}}"><span><strong>{{p}}</strong>：{{a}}</span></label></div>{% endfor %}<button>正解人数とお題を公開</button></form></section>
{% elif phase == 'result' %}<section class="card"><span class="badge">結果</span><h2>{{question}}</h2><p>正解：<strong>{{answer}}</strong></p><p>正解者数：<strong>{{correct_count}}人</strong> ／ 目標：<strong>{{target}}人</strong></p><p>出題者の得点：{% if correct_count == target %}目標ぴったりで3点{% elif (correct_count-target)|abs == 1 %}目標との差が1人で{{ 0 if players|length == 3 else (2 if players|length == 6 else 1) }}点{% else %}今回は0点{% endif %}。正解者にも1点ずつ加算しました。</p><div class="row"><form method="post" action="/next"><button>次のラウンド</button></form><form method="post" action="/reset"><button class="secondary">最初から</button></form></div></section>{% endif %}
{% endif %}</main><script>
let playerCount={{count or 3}};
function renderNames(){document.getElementById('count').textContent=playerCount;document.getElementById('countInput').value=playerCount;document.getElementById('minusButton').classList.toggle('secondary',playerCount===3);document.getElementById('plusButton').classList.toggle('secondary',playerCount===6);const box=document.getElementById('nameFields');if(!box)return;box.replaceChildren();box.classList.add('name-grid');for(let i=0;i<playerCount;i++){const field=document.createElement('div');field.className='name-field';field.style.gridColumn=i<3?'1':'2';field.style.gridRow=String(i%3+1);const label=document.createElement('label');label.textContent=`参加者 ${i+1} の名前`;const input=document.createElement('input');input.name='player';input.required=true;input.placeholder=`例：プレイヤー${i+1}`;field.append(label,input);box.append(field)}}
function changeCount(delta){playerCount=Math.max(3,Math.min(6,playerCount+delta));renderNames()}renderNames();
</script></body></html>"""

def render(msg=None):
    data = session.get("game", {})
    players = data.get("players", [])
    answerers = [p for p in players if p != data.get("setter")]
    answer_index = len(data.get("answers", []))
    current_answerer = answerers[answer_index] if answer_index < len(answerers) else ""
    return render_template_string(PAGE, msg=msg, count=request.args.get("count", 3, type=int), players=players, answerers=answerers, current_answerer=current_answerer, scores=data.get("scores", {}), **{k:v for k,v in data.items() if k not in ("players", "scores")})

@app.get("/")
def home(): return render()

@app.post("/start")
def start():
    players = [x.strip() for x in request.form.getlist("player") if x.strip()]
    if not 3 <= len(players) <= 6: return render("参加者は3〜6人で入力してください。")
    if len(set(players)) != len(players): return render("名前は重複しないようにしてください。")
    session["game"] = {"players":players,"scores":{p:0 for p in players},"round_no":1}
    return redirect(url_for("next_round"))

@app.post("/next")
@app.get("/next")
def next_round():
    g=session.get("game")
    if not g: return redirect("/")
    previous_setter=g.get("setter")
    candidates=[p for p in g["players"] if p != previous_setter]
    g.update(phase="confirm",setter=random.choice(candidates),target=random.randint(1,len(g["players"])-1),question="",answer="",answers=[])
    session["game"]=g
    return render()

@app.post("/show_prompt")
def show_prompt():
    g=session.get("game")
    if not g: return redirect("/")
    if g.get("phase") != "confirm": return redirect("/")
    g["phase"]="setup"
    session["game"]=g
    return redirect("/")

@app.post("/question")
def question():
    g=session.get("game")
    if not g: return redirect("/")
    q=request.form.get("question", "").strip(); a=request.form.get("answer", "").strip()
    if not q or not a: return render("質問と正解を入力してください。")
    g.update(phase="answers",question=q,answer=a,answers=[])
    session["game"]=g
    return redirect("/")

@app.post("/submit_answer")
def submit_answer():
    g=session.get("game")
    if not g: return redirect("/")
    answerers=[p for p in g["players"] if p != g["setter"]]
    i=len(g.get("answers", []))
    a=request.form.get("answer", "").strip()
    if not a: return render("回答を入力してください。")
    if i >= len(answerers): return redirect("/")
    g.setdefault("answers", []).append([answerers[i],a])
    if len(g["answers"]) >= len(answerers): g["phase"]="mark"
    session["game"]=g
    return redirect("/")

@app.post("/reveal")
def reveal():
    g=session.get("game")
    if not g: return redirect("/")
    indexes={int(x) for x in request.form.getlist("correct")}
    count=sum(1 for i in indexes if 0 <= i < len(g["answers"]))
    for i,(p,_) in enumerate(g["answers"]):
        if i in indexes: g["scores"][p]+=1
    if count == g["target"]:
        g["scores"][g["setter"]] += 3
    elif abs(count - g["target"]) == 1:
        g["scores"][g["setter"]] += {3: 0, 4: 1, 5: 1, 6: 2}[len(g["players"])]
    g.update(phase="result",correct_count=count)
    session["game"]=g
    return redirect("/")

@app.post("/reset")
def reset(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(debug=True)
