# 豊聡耳（とよとみみ）

音声ファイルを与えると、AI が会話の声を分析し、**発話者ごとに分けて文字起こし**するデスクトップアプリです。

- 話者分離（誰が話したか）＋文字起こし（何を話したか）を同時に実行
- 処理方法を切替可能なハイブリッド構成
  - **クラウド**: [AssemblyAI](https://www.assemblyai.com/)（高速・高精度・要 API キー）
  - **ローカル**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) + [pyannote.audio](https://github.com/pyannote/pyannote-audio)（オフライン・無料・要 HF トークン）
- 結果を `txt` / `srt` / `json` で保存可能
- **uv で Python 3.11 を固定**しているため、システムの Python が更新されてもアプリは壊れません

> 操作・仕様の詳細は [ユーザーガイド](docs/ユーザーガイド.md) を参照してください。

## 必要なもの

- [uv](https://docs.astral.sh/uv/)（Python のバージョン管理とパッケージ管理を行う）
- [ffmpeg](https://ffmpeg.org/)（音声形式の変換に使用。PATH を通しておく）
- 利用する処理方法に応じたキー
  - クラウド: AssemblyAI の API キー
  - ローカル: Hugging Face トークン（下記 3 モデルの利用規約に同意。無料）
    - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
    - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
    - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)

## セットアップ

uv が未導入の場合は次のいずれかで導入します。

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# もしくは pip 経由
pip install uv
```

依存をインストールします。`.python-version` に従い uv が Python 3.11 を自動で用意します。

```powershell
# クラウド処理だけ使う場合（軽量）
uv sync --extra cloud

# ローカル処理も使う場合（torch などを含むため大きめ）
uv sync --extra local

# 両方
uv sync --extra cloud --extra local
```

> `uv` コマンドが見つからない場合は、フルパスで実行できます:
> `& "$env:USERPROFILE\.local\bin\uv.exe" sync --extra cloud`

### 処理方法ごとのパッケージ（事前インストール）

GUI 本体（PySide6 など）だけでは文字起こしエンジンは入りません。**初めてその処理方法を使う前に**、上記 `uv sync --extra ...` を実行してください。

| 処理方法 | コマンド | 主な追加パッケージ |
|----------|----------|-------------------|
| **クラウド** | `uv sync --extra cloud` | `assemblyai` |
| **ローカル** | `uv sync --extra local` | `faster-whisper`, `pyannote.audio`, `torch` など |
| **両方** | `uv sync --extra cloud --extra local` | 上記すべて |

- **クラウドだけ使う**場合は `--extra cloud` だけで十分です（数 MB 程度）。
- **ローカルだけ使う**場合は `--extra local` を実行してください（torch などを含むため数 GB 級）。
- **処理方法を切り替えて使う**場合は、最後に `--extra cloud --extra local` を実行して両方入れておくと安全です。`--extra cloud` だけ実行するとローカル用パッケージが外れ、逆も同様です。
- パッケージを追加・更新したあとは、**豊聡耳を再起動**してから解析してください。

クラウド処理で `assemblyai がインストールされていません` と表示された場合も、プロジェクトフォルダで `uv sync --extra cloud` を実行すれば解消します。

キーを設定します。`.env.example` をコピーして編集してください。

```powershell
copy .env.example .env
# .env に ASSEMBLYAI_API_KEY / HF_TOKEN を記入
```

> キーはアプリ内の「設定」画面からも入力・保存できます（`~/.toyotomimi/config.json`）。環境変数が設定されている場合はそちらが優先されます。

## 起動

```powershell
# 方法1: uv が PATH に入っている場合
uv run toyotomimi

# 方法2: 仮想環境から直接起動（uv が PATH に無い場合も使える）
.\.venv\Scripts\toyotomimi.exe
```

> **`uv` コマンドが見つからない**（PowerShell で `CommandNotFoundException` が出る）場合:
>
> - **原因:** uv が未インストール、またはインストール済みでも PATH に入っていない（ターミナルを開き直していない）
> - **対処:** 下記のいずれか
>   - 上記 [セットアップ](#セットアップ) で uv をインストールし、**PowerShell を一度閉じて開き直す**
>   - 上記 **方法2** で起動する（`uv sync` 済みで `.venv` がある場合）
>   - uv のフルパスで実行する: `& "$env:USERPROFILE\.local\bin\uv.exe" run toyotomimi`
>   - ユーザー PATH に `%USERPROFILE%\.local\bin` を追加して PowerShell を開き直す
>
> 方法2 は **`uv sync` 実行後** に生成される `.venv` が必要です。`.venv` が無い場合は先にセットアップを完了してください。

1. 「ファイルを選択」で音声ファイル（mp3 / wav / m4a など）を指定（**PC 上のどこに置いてもよい**。プロジェクトフォルダへのコピーは不要）
2. 処理方法（クラウド / ローカル）を選択
3. 「解析する」を押す
4. 話者ごとに分かれた文字起こしが表示される
5. 「結果を保存」で `txt` / `srt` / `json` に出力

## 構成

```
src/toyotomimi/
  __main__.py           # エントリ（GUI 起動）
  config.py             # 設定の読み書き
  models.py             # SpeakerSegment / TranscriptResult
  audio.py              # ffmpeg で 16kHz mono へ変換
  export.py             # txt / srt / json 出力
  engines/
    base.py             # TranscriptionEngine 抽象基底
    cloud_engine.py     # AssemblyAI
    local_engine.py     # faster-whisper + pyannote
  gui/
    main_window.py      # メイン画面
    worker.py           # QThread ワーカー
    settings_dialog.py  # 設定ダイアログ
```

## 使用する API と上限

処理方法ごとに使う外部サービスが異なります。**クラウドとローカルで必要なキーも別**です。

| 処理方法 | 認証 | 使う API / サービス | このアプリでの用途 |
|----------|------|---------------------|-------------------|
| **クラウド** | `ASSEMBLYAI_API_KEY` | [AssemblyAI](https://www.assemblyai.com/) Transcription API | 話者分離付き文字起こし（1 API で完結） |
| **ローカル** | `HF_TOKEN` | [Hugging Face Hub](https://huggingface.co/) | pyannote 話者分離モデルのダウンロード・利用規約同意済みリポジトリへのアクセス |

> **HF トークンはローカル処理専用**です。クラウド処理では AssemblyAI の API キーのみ使い、Hugging Face には接続しません。

### クラウド（AssemblyAI）

- **API の種類**: Pre-recorded Speech-to-Text（`speaker_labels=True` で話者ラベル付き）
- **課金・上限**（[公式 Pricing / FAQ](https://www.assemblyai.com/pricing) 参照）:
  - 新規登録で **$50 分の無料クレジット**（クレジットカード不要）
  - クレジットは **使い切るまで有効**（毎月リセットではない）
  - 無料枠では **同時実行の文字起こしは最大 5 件**
  - アカウント全体で **5 分あたり最大 20,000 リクエスト** のレート制限
- **目安**: 話者分離を含む文字起こしは音声の長さに応じてクレジットを消費します。長時間・大量処理の場合は [料金ページ](https://www.assemblyai.com/pricing) で残高を確認してください。

### ローカル（Hugging Face + ローカルモデル）

- **HF トークンが必要な理由**: [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) など **gated モデル**へのアクセスのため（Read 権限で十分）
- **HF トークンが不要な部分**:
  - [faster-whisper](https://github.com/SYSTRAN/faster-whisper) による文字起こし（Hub とは別経路でモデルを取得）
  - 2 回目以降の解析（モデルは `~/.cache/huggingface/` 等にキャッシュされ、Hub への通信はほぼ発生しない）
- **Hub のレート制限**（[公式ドキュメント](https://huggingface.co/docs/hub/rate-limits) 参照）:
  - 無料ユーザー: **5 分あたり API リクエスト約 1,000 件**（2025年9月時点の目安）
  - 上限超過時は **429 Too Many Requests** が返る
  - トークン未設定の匿名アクセスより、`HF_TOKEN` を付けた方が上限は高い
- **403 エラー**: レート制限ではなく、**利用規約未同意**が原因のことが多いです（上記 3 モデルすべてで **Agree and access repository** が必要）

### どちらを選ぶか

| | クラウド | ローカル |
|--|---------|---------|
| 必要なキー | AssemblyAI API キー | HF トークン |
| 主な上限 | クレジット残高・同時実行数 | Hub ダウンロード時のレート制限（初回のみ） |
| 解析ごとの API 消費 | あり（音声長に比例） | 初回 DL 後は基本なし |
| オフライン | 不可 | モデル DL 後は可能 |

## 注意点

- **`uv run toyotomimi` で `CommandNotFoundException`:** パッケージ不足ではなく **uv 自体が使えない**状態です。上記 [起動](#起動) の対処を参照してください。
- GPU が無い環境では `torch` の **CPU 版** を使用します（`pyproject.toml` で設定済み）。ローカル処理は長い音声だと時間がかかります（1時間の音声で数十分かかることもあります）。
- pyannote のモデルは初回実行時に Hugging Face からダウンロードされます。**初回のローカル解析はモデル DL のため、完了まで十数分かかることがあります。**
- **403 エラー**が出る場合は、上記 3 モデルすべてで **Agree and access repository** を押したか確認してください。同意漏れがあると、**モデル名が変わりながら 403 が続く**ことがあります（例: `segmentation-3.0` → `speaker-diarization-community-1`）。
- **Hugging Face トークン**は **Read** 権限で十分です（Fine-grained でも可だが、gated モデルの読み取り権限が必要）。**Google / Gemini のトークンは使えません。**
- Hugging Face 登録直後の「組織に参加」画面は**スキップして問題ありません**（個人利用なら組織は不要）。
- **ffmpeg** をインストールした直後は、**豊聡耳を再起動**してください。起動中のアプリは古い PATH を参照し、「ffmpeg が見つかりません」と表示されることがあります（Windows では winget 経由の ffmpeg を自動検出します）。
- **uv** や **ffmpeg** を PATH に追加したあとも、**PowerShell やアプリを開き直す**と反映されます。
- ローカル処理が CUDA を検出した場合は自動的に GPU を使用します。
- Windows のローカル処理では pyannote 4.x の都合で音声をメモリ上の波形として渡しています（torchcodec 非依存）。ユーザー側の追加設定は不要です。

## ライセンス

MIT
