---
title: Claude のモデル提供終了、猶予は告知から約60日 ― 過去9回を数えて、手元を検査するスクリプトを書いた
tags:
  - ClaudeCode
  - AIエージェント
  - 生成AI
  - AI
  - 個人開発
private: false
updated_at: '2026-09-01T21:01:43+09:00'
id: bc2a7be2a6ee4ceb6185
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---

公式のモデル提供終了ページを見ていて、読み間違えかけました。

```
claude-sonnet-4-5-20250929    Not sooner than September 29, 2026
```

**「9月29日に消える」と読みました。違いました。**

この記事は、その読み間違いを直すところから始めて、**過去9回の提供終了が実際に何日の猶予だったかを数え**、**自分の環境に日付つきIDが何か所埋まっているかを検査する**までを書きます。数字はすべて一次情報から数えたものです。推測は書きません。

（すべて 2026年9月1日時点の記載に基づきます。日付や状態はあとから変わります。**必ず一次情報を確認してください。**）

## まず、読み方を間違えていた

一次情報は Anthropic のモデル提供終了ページです。そこにある表から、Claude 4.5 系の3行を引きます。

```
API model name                Current state   Deprecated   Tentative retirement date
claude-sonnet-4-5-20250929    Active          N/A          Not sooner than September 29, 2026
claude-haiku-4-5-20251001     Active          N/A          Not sooner than October 15, 2026
claude-opus-4-5-20251101      Active          N/A          Not sooner than November 24, 2026
```

見るべき列は3つあります。

```
Current state  = Active    まだ現役。非推奨にすらなっていない
Deprecated     = N/A       **廃止の告知が、まだ出ていない**
Tentative      = Not sooner than …   「これより早くはならない」最短日
```

**Tentative retirement date は確定日ではありません。**「暫定」であり、しかも "Not sooner than"、つまり**下限**です。9月29日に消えるという意味ではありません。

そして `Deprecated` が `N/A` である以上、**告知はまだ出ていません。**このページの定義では、Deprecated になってはじめて「非推奨」であり、そこで退役日が割り当てられます。

**私は最短日を確定日と読み、告知を見落としていたと思い込みました。**そうではなく、告知はまだ来ていない、が正しい読みです。

## では、告知が来たら何日あるのか ― 過去9回を数えた

ここが本題です。公式の記述はこうです。

> 一般提供されたモデルについては、退役の少なくとも60日前に通知する

「少なくとも60日」が実際にどう運用されてきたかは、同じページの提供終了履歴に全部載っています。**告知日と退役日を引き算しました。**

```
告知日        退役日        日数   対象
2024-09-04   2024-11-06     63   Claude 1 / Instant
2025-01-21   2025-07-21    181   Claude 2 / 2.1 / Sonnet 3
2025-06-30   2026-01-05    189   Opus 3
2025-08-13   2025-10-28     76   Sonnet 3.5
2025-10-28   2026-02-19    114   Sonnet 3.7
2025-12-19   2026-02-19     62   Haiku 3.5
2026-02-19   2026-04-20     60   Haiku 3
2026-04-14   2026-06-15     62   Sonnet 4 / Opus 4
2026-06-05   2026-08-05     61   Opus 4.1
```

**直近4回は 62 / 60 / 62 / 61 日です。**

```
全9回     最短 60日   最長 189日
直近5回   114, 62, 60, 62, 61   中央値 62日
```

かつては181日や189日の猶予がありました。**いまは公式が約束する下限（60日）に張り付いています。**

これは非難ではありません。**運用の前提が変わったという事実です。**

```
昔の感覚   告知が来てから半年かけて移せた
いまの実績 **告知から2か月。テストと再検証を含めて2か月**
```

数える前、私は「まだ先の話」と思っていました。**数えたら、告知が来てから動くのでは遅い運用が自分にありました。**

## 何が止まるのか ― 日付つきIDだけ

止まるのは**日付つきのモデルID**を文字列で固定している箇所です。

```
止まる    claude-sonnet-4-5-20250929   ← 日付つき。そのバージョンが退役したら失敗する
止まらない claude-sonnet-4-6            ← エイリアス。指す先が更新される
```

厄介なのは、**この文字列は一度書くと、動いている限り二度と読み返されない**ことです。動いているコードは開かれません。**期日が来るまで誰も気づきません。**

しかも埋まる場所が散らばります。

```
SDK 呼び出しの model= 引数
エージェント定義ファイル
CI / GitHub Actions の環境変数
設定 YAML・JSON
ドキュメントに書いたサンプル（コピーされて広がる）
```

## だから、告知が来る前に数えた

告知が来てから探すと、**探す場所が分からない**状態から始まります。先に数えておけば、告知の日は「置換するだけ」になります。

検査するスクリプトを書きました。**外部通信をしません。ファイルを読んで数えるだけです。**

```python
# -*- coding: utf-8 -*-
"""日付つきモデルIDが、手元に何か所埋まっているかを数える。

    python scan_model_ids.py <対象ディレクトリ> [...]

**中身は出さない。数と、拡張子と、行番号だけ。**
"""
from __future__ import annotations
import io, os, re, sys, collections

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# claude-<なにか>-YYYYMMDD 形式。これが「止まる書き方」
DATED = re.compile(r'claude-[a-z0-9.\-]*?-(20\d{6})\b')

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}
TEXT_EXT = {'.py', '.js', '.ts', '.tsx', '.json', '.yaml', '.yml', '.toml', '.md',
            '.sh', '.bat', '.ps1', '.txt', '.env', '.cfg', '.ini'}


def scan(roots):
    dated = collections.Counter()
    hits = []
    files = 0
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in TEXT_EXT:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) > 2_000_000:
                        continue
                    text = io.open(p, encoding='utf-8', errors='ignore').read()
                except OSError:
                    continue
                files += 1
                for i, line in enumerate(text.splitlines(), 1):
                    for m in DATED.finditer(line):
                        dated[m.group(0)] += 1
                        hits.append((p, i, m.group(0), ext))
    return files, dated, hits


def main():
    roots = sys.argv[1:] or ['.']
    files, dated, hits = scan(roots)
    print(f'走査したテキストファイル {files:,} 件')
    print(f'\n日付つきモデルID  出現 {sum(dated.values())} 回 / 種類 {len(dated)}')
    for k, v in dated.most_common():
        print(f'   {k:34s} {v:4d}回')
    if hits:
        ext = collections.Counter(h[3] for h in hits)
        print('\n埋まっていたファイル種別')
        for k, v in ext.most_common():
            print(f'   {k:10s} {v:4d}箇所')
    else:
        print('\n日付つきIDは見つからなかった。')


if __name__ == '__main__':
    main()
```

使い方はこれだけです。

```bash
python scan_model_ids.py ~/your-repo ~/another-repo ~/.claude
```

## 自分の環境を検査した結果 ― 0件でした

正直に書きます。**私の環境では、コードに日付つきIDは1件もありませんでした。**

```
走査したテキストファイル 1,048 件
日付つきモデルID  出現 10 回 / 種類 3
   claude-sonnet-4-5-20250929   4回
   claude-haiku-4-5-20251001    3回
   claude-opus-4-5-20251101     3回

埋まっていたファイル種別
   .md          10箇所
```

**10回すべて `.md` です。**中身を確認したら、**この記事を書くために作った自分のメモでした。**実行される場所には1件もありませんでした。

拍子抜けですが、これが検査の正しい結果です。**そして「0件だと分かっている」ことと「調べていない」ことは、まったく別の状態です。**告知が来た日に、私はもう探さなくて済みます。

なお、この記事の10件は「拡張子ごとの内訳」を出したから正体が分かりました。**種別の内訳を出さない検査だと、`.md` の10件を「10か所直す必要がある」と読み違えます。**数を出す検査は、必ず内訳も出してください。

## APIを実際に叩いている人は、Console でも監査できる

コードを読む検査は「書いてある場所」しか見つけません。**実際に何を呼んだか**は、Console の Usage ページから CSV を書き出せば、APIキーとモデルごとの内訳が取れます。公式が案内している手順です。

```
コードを読む   書いてあるが動いていないものも見つかる
実績を見る     動いているが書いた覚えのないものが見つかる
```

**両方やらないと片側が抜けます。**私はコード側しかやっていません。ここは実測していないので、そう書いておきます。

## 「全部エイリアスにしろ」ではない

ここまで読むと「日付つきIDをやめてエイリアスにすればいい」と読めますが、そう単純ではありません。

**日付つきIDが正しい場面があります。**

```
エイリアスが向く   動き続けることが最優先。多少挙動が変わってもよい
                   運用の自動化、社内ツール、実験の足回り
日付つきが向く     **結果を再現できることが最優先**
                   評価・ベンチマーク、論文や記事に載せた数字、
                   回帰テストの基準値
```

エイリアスは指す先が黙って変わります。**「先週と同じプロンプトで結果が違う」の原因になり得ます。**再現性を担保したい場所で日付つきIDを使うのは、正しい設計です。

**問題は「どちらを選んだか意識せずに書いた日付つきID」です。**私が数えようとしたのはそれで、区別は検査では付きません。**付けられるのは、書いた本人だけです。**

だから検査の出力は「直すべき箇所」ではなく「**確認すべき箇所**」として読んでください。

## 移行先の暫定退役日も、同じ表に載っている

移す先にも同じ列があります。2026年9月1日時点の Active なモデルを、暫定退役日の近い順に並べます。

```
claude-sonnet-4-5-20250929   Not sooner than 2026-09-29    28日後
claude-haiku-4-5-20251001    Not sooner than 2026-10-15    44日後
claude-opus-4-5-20251101     Not sooner than 2026-11-24    84日後
claude-opus-4-6              Not sooner than 2027-02-05
claude-sonnet-4-6            Not sooner than 2027-02-17
claude-opus-4-7              Not sooner than 2027-04-16
claude-opus-4-8              Not sooner than 2027-05-28
claude-fable-5               Not sooner than 2027-06-09
claude-sonnet-5              Not sooner than 2027-06-30
claude-opus-5                Not sooner than 2027-07-24
```

**移行先を選ぶときは、その移行先の暫定日も見てください。**近いものへ移すと、同じ作業をすぐもう一度やることになります。

## まとめ

```
1  "Not sooner than 9月29日" は「9月29日に消える」ではない
   Deprecated が N/A のうちは、**告知すら出ていない**
2  告知から退役まで、直近4回は **62 / 60 / 62 / 61 日**
   かつては181日・189日もあった。**いまは公式の下限に張り付いている**
3  止まるのは日付つきID。エイリアスなら止まらない
4  告知が来てから探すと、探す場所が分からないところから始まる
   **先に数える。**数えるのは数分で終わる
5  数える検査は、必ず**内訳**も出す。出さないと自分のメモを事故と読む
```

**この記事でいちばん役に立つのは、たぶん 2 です。**「まだ先の話」という感覚と、実績の60日には、ずれがあります。

---

数字はすべて 2026年9月1日時点の一次情報から数えました。**日付と状態は変わります。**移行の判断をする前に、必ず公式のページで現在の状態を確認してください。

---

## この連載

AIエージェントを実際に回して、かかった費用と壊れた箇所を測って書いています。**推測は書きません。実測値だけです。**

1. Claude Code のトークン使用量を実測したら1ターン23万 ― 節約に効いたのは「セッションを切る」だった
   https://qiita.com/manabu49-ai/items/2598a30d5140e4445ab6
2. 57分間、死んだジョブを誰も見ていなかった ― AIエージェントの見張りを機械に渡す
   https://qiita.com/manabu49-ai/items/5c7506c94b5be58c040e
3. AIに100通り試させたら、効果ゼロなのに5個が「有意」だった
   https://qiita.com/manabu49-ai/items/397a018948e1ab7ef29e
4. 次 ― 仕様書を読まずに対処を実装して、欠測を作りかけた話（未公開）

番外 ― **本記事** ― Claude のモデル提供終了、猶予は告知から約60日 ― 過去9回を数えて、手元を検査するスクリプトを書いた

**無料記事は結論まで全部書きます。**出し惜しみはしません。
