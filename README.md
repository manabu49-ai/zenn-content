# zenn-content

**Zenn の GitHub 連携用リポジトリ。**push すると zenn.dev へ自動同期される。

## ここに置くもの / 置かないもの

```
⭕ articles/*.md   公開する記事だけ
⭕ images/         記事に使う画像
❌ 事業計画・実測ログ・戦略メモ
   → それらは ~/ai-ops-writing に置く。**このリポジトリには入れない**
```

**理由: このリポジトリは GitHub にあり、Zenn からも読まれる。**
**公開してよいものだけを置く。**

## ファイルの規則（Zenn公式）

```
場所      articles/{slug}.md
slug      a-z0-9 と - _ の **12〜50字**。あとから変更できない
```

**フロントマター**

```yaml
---
title: "記事のタイトル"
emoji: "⏰"          # 1文字
type: "tech"         # tech（技術記事） or idea
topics: ["python", "windows", "運用", "claudecode", "ai"]
published: false     # ★既定は false。公開するときだけ true にする
---
```

## 公開の手順

```
1  記事を articles/ に書く（published: false のまま）
2  ~/ai-ops-writing/scripts/guard.py を通す → 検出0件を確認
3  禁止語を grep    競馬|馬券|オッズ|回収率|JRA|単勝  → 0件を確認
4  published: true に変える   ← **これが公開の意思表示**
5  git commit && git push     → 数分で zenn.dev に出る
```

**push した瞬間に公開される。**
**だから既定を false にしてある。**`true` に変える操作を、公開ボタンの代わりにする。

## 注意

```
・連携できるリポジトリは **最大2つ**
・記事の削除は **Zennのダッシュボードから**行う
  （リポジトリから消すだけでは、再pushで復活する）
・Fork からのプルリクエストはデプロイされない
・slug は後から変えられない。**変えると別記事として作られる**
```

## すでに Web エディタで公開した記事について

**005「57分間、死んだジョブを誰も見ていなかった」は Web エディタで公開済み。**

**この記事を articles/ に置いて push してはいけない。**
別 slug の**二重投稿**になる。

**GitHub 連携は 004 から始める。**

---

## ホームページ（GitHub Pages）

```
docs/                    公開されるサイト本体（自動生成）
scripts/build_site.py    生成スクリプト
site.config.json         サイト名・URL・各サービスのユーザー名
```

**Zenn が読むのは `articles/` と `images/` だけ。`docs/` を置いても同期には影響しない。**

### 更新のしかた

```
1  site.config.json を編集する（プロフィール文・ユーザー名など）
2  python3 scripts/build_site.py     → docs/index.html と sitemap.xml が再生成される
3  git commit && git push            → 数分で公開URLに反映される
```

記事一覧は `articles/*.md`（`published: true`）と `public/*.md`（Qiita 投稿済み）から自動で作られる。
**記事を足したら 2 を実行し直す。**手で `docs/index.html` を編集しても次の生成で消える。

### 公開URLを有効にする（最初の一回だけ）

```
GitHub → Settings → Pages
  Source  : Deploy from a branch
  Branch  : main  /  フォルダは  /docs
  Save
```

数分後に `https://manabu49-ai.github.io/zenn-content/` が開く。

### 検索に載せる

```
1  Google Search Console に上記URLを登録する（所有権の確認はDNSではなくHTMLタグで可）
2  サイトマップに  sitemap.xml  を送信する
3  インデックス登録はリクエストしてから数日〜数週間かかる
```

**Yahoo! JAPAN の検索結果は Google のインデックスを使っている。**
**Google に載れば Yahoo! にも載る。Yahoo! 向けの個別作業は要らない。**

### 注意

```
・robots.txt はドメイン直下しか読まれない
  → /zenn-content/robots.txt は無視される（既定が「全許可」なので実害はない）
・ルートURL（https://manabu49-ai.github.io/）にしたい場合は
  manabu49-ai.github.io という名前の別リポジトリを作り、docs/ の中身をそこに移す
  そのときは site.config.json の base_url も直す
```
