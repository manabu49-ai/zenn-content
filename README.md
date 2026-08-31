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
