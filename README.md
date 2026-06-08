# 豊聡耳（とよとみみ）

音声ファイルを与えると、AI が会話の声を分析し、**発話者ごとに分けて文字起こし**するデスクトップアプリです。

- 話者分離（誰が話したか）＋文字起こし（何を話したか）を同時に実行
- 処理方法を切替可能なハイブリッド構成
  - **クラウド**: [AssemblyAI](https://www.assemblyai.com/)（高速・高精度・要 API キー）
  - **ローカル**: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) + [pyannote.audio](https://github.com/pyannote/pyannote-audio)（オフライン・無料・要 HF トークン）
- 結果を `txt` / `srt` / `json` で保存可能
- **uv で Python 3.11 を固定**しているため、システムの Python が更新されてもアプリは壊れません

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

> `uv` コマンドが見つからない場合は、次のいずれかで対処できます。
>
> - 上記 **方法2** で起動する
> - uv のフルパスで実行する: `& "$env:USERPROFILE\.local\bin\uv.exe" run toyotomimi`
> - ユーザー PATH に `%USERPROFILE%\.local\bin` を追加して PowerShell を開き直す

1. 「ファイルを選択」で音声ファイル（mp3 / wav / m4a など）を指定
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

## 注意点

- GPU が無い環境では `torch` の **CPU 版** を使用します（`pyproject.toml` で設定済み）。ローカル処理は長い音声だと時間がかかります。
- pyannote のモデルは初回実行時に Hugging Face からダウンロードされます。403 エラーが出る場合は、上記 3 モデルすべてで **Agree and access repository** を押したか確認してください。
- ローカル処理が CUDA を検出した場合は自動的に GPU を使用します。

## ライセンス

MIT
