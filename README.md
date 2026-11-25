# AI歌合

十六番の歌合を Claude のサブエージェントで催した記録と、その観覧サイト。

- 判者：Fable・Opus・Sonnet（各一名）
- 左方・右方：それぞれ Fable・Opus・Sonnet・Haiku（計八名）
- すべて effort = medium、人物設定なし
- 兼題。左右は独立に詠み、判は作者を伏せて行う。持なし、三判者の多数決。
- 組合せは 4×4 のラテン方陣（どの左の歌人もどの右の歌人と一度ずつ当たる）。

## 記録

| ファイル | 内容 |
|---|---|
| `data/utaawase.json` | 全記録（題・歌・作者・判・判詞・勝敗）。サイトはこれを読む |
| `data/schedule.json` | 題と組合せ（`scripts/setup.py` が seed 付きで生成） |
| `data/raw/01_dai_suggestions.json` | 三判者の題の案（各八題。うち十六を主催者が選定） |
| `data/raw/02_poems.json` | 歌人ごとの詠草と依頼文の雛形 |
| `data/raw/judge_prompt.txt` | 判者に渡した文面（作者なし） |
| `data/raw/03_judgments.json` | 判者ごとの判と判詞 |
| `data/raw/discarded_left_first_draft.json` | 不採用の初稿（方式変更のため詠み直し） |

`python3 scripts/build.py` で raw から `data/utaawase.json` を作り直せる。

## サイト

静的サイト（`index.html` / `style.css` / `app.js`）。`python3 -m http.server` で開くか、GitHub Pages で公開する。
好きな方の歌を選ぶと作者と判が明かされ、判者を押すと判詞が出る。「記録」は自分が判じた番だけを集計する。
