"""Build the 題 list and the matchup schedule (seeded, reproducible)."""
import json, random
SEED = 20261125
MODELS = ["fable", "opus", "sonnet", "haiku"]
# (題, よみ, 部, 提案した判者, 趣意)
DAI = [
 ("霞隔遠樹","かすみゑんじゅをへだつ","春","fable","遠山の木立を霞がへだてる朧な眺望。見えそうで見えぬ景に春の心を寄せる結題。"),
 ("夕花","ゆふべのはな","春","opus","暮れてゆく光のなかの花で、散る惜しみに一日の終わりが重なる"),
 ("春月","しゅんげつ","春","sonnet","朧にかすむ春の夜の月。艶と哀れを兼ねた伝統的な題。"),
 ("雨後郭公","うごのほととぎす","夏","fable","五月雨の晴れ間に聞く一声。待つ心と雨の名残の湿りを取り合わせる。"),
 ("水上蛍","みづのうへのほたる","夏","opus","火と水の取り合わせで、映る光と思ひの火への転じ方を見る"),
 ("夏草","なつくさ","夏","sonnet","茂り乱れる草のいきれに、時の移ろいと人の跡の絶えたさまを託す。"),
 ("月前擣衣","げつぜんのたうい","秋","opus","砧の音と月光を取り合わせ、聴覚と視覚の両方で秋夜の寂しさを詠ませる"),
 ("野径虫声","やけいのちゅうせい","秋","fable","露深い野の小道に分け入って聞く虫の音。行く人の袖と心細さを詠み込む、やや新味の題。"),
 ("秋夕","あきのゆうべ","秋","sonnet","『秋の夕暮』の寂しさを正面から詠む。古来の名題に挑む一番。"),
 ("暁天千鳥","げうてんのちどり","冬","fable","冬の明け方、川風や浦波に鳴く千鳥。寝覚めの寒さと寂寥を本意とする。"),
 ("初雪待つ夜","はつゆきまつよ","冬","sonnet","まだ降らぬ雪を待つ心。冬の入口の静けさを結題で新たに。"),
 ("寄燈忍恋","ともしびによするしのぶこひ","恋","fable","人知れぬ思いを、かきたてても消えがての燈火に寄せる。寄物の新しみを狙った恋題。"),
 ("寄鏡恋","かがみによするこひ","恋","opus","映る面影と曇る鏡で、恋の自省と変わる心を詠ませる寄物題"),
 ("返事なき文","かえりごとなきふみ","恋","sonnet","送った文に応えのない待つ身の切なさ。やや新味のある結題。"),
 ("逢不遇恋","あひてあはざるこひ","恋","opus","一度逢ってから隔てられた恋で、恨みと追憶の間の機微を競わせる"),
 ("山家暮鐘","さんかのぼしょう","雑","fable","山住みの夕べに聞く入相の鐘。閑寂と無常、述懐の心を自由に詠ませる。"),
]
rng = random.Random(SEED)
# Latin-square schedule: 4 blocks of 4 rounds; every poet appears once per block,
# every left×right pairing occurs exactly once over 16 rounds.
perm = MODELS[:]; rng.shuffle(perm)
shifts = [0,1,2,3]; rng.shuffle(shifts)
pairs = []
for s in shifts:
    block = [(MODELS[i], perm[(i+s)%4]) for i in range(4)]
    rng.shuffle(block)
    pairs += block
rounds = [dict(ban=n+1, dai=d[0], yomi=d[1], bu=d[2], dai_by=d[3], dai_note=d[4],
               left=dict(model=l), right=dict(model=r), judgments=[])
          for n,(d,(l,r)) in enumerate(zip(DAI,pairs))]
json.dump(dict(seed=SEED, rounds=rounds), open("data/schedule.json","w"), ensure_ascii=False, indent=1)
for r in rounds: print(r["ban"], r["dai"], r["left"]["model"], r["right"]["model"])
