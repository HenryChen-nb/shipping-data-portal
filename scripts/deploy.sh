#!/usr/bin/env bash
# 部署到 GitHub Pages（gh-pages 分支）
# 用法: ./scripts/deploy.sh <repo-url> [提交信息]
#   例: ./scripts/deploy.sh git@github.com:HenryChen-nb/global-shipping-data.git
#   例: ./scripts/deploy.sh https://github.com/HenryChen-nb/global-shipping-data.git "站点更新"
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 1 ]; then
  echo "用法: $0 <repo-url> [提交信息]"
  echo "  repo-url 可以是 https://github.com/<user>/<repo>.git 或 git@github.com:<user>/<repo>.git"
  exit 1
fi
REPO="$1"
MSG="${2:-站点更新 $(date +%F)}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> 准备 gh-pages 分支 ..."
if git clone --depth 1 --branch gh-pages "$REPO" "$TMP" 2>/dev/null; then
  echo "    已检出现有 gh-pages"
elif git clone --depth 1 "$REPO" "$TMP" 2>/dev/null; then
  (cd "$TMP" && git checkout --orphan gh-pages && git rm -rf . >/dev/null 2>&1 || true)
  echo "    已从默认分支创建 gh-pages"
else
  echo "    仓库不存在，初始化 gh-pages"
  mkdir -p "$TMP"
  git -C "$TMP" init -q
  git -C "$TMP" checkout --orphan gh-pages
fi

echo "==> 同步站点文件 ..."
rsync -a --delete --exclude '.git' --exclude 'data/cache' ./ "$TMP/"

echo "==> 提交并推送 ..."
git -C "$TMP" add -A
git -C "$TMP" commit -m "$MSG" -q
git -C "$TMP" push origin gh-pages
echo "==> 部署完成。访问: https://<user>.github.io/<repo>/"
