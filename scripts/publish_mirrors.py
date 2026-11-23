"""Publish a release and its binary assets to Gitee and GitCode.

GitHub releases are handled by ``scripts/publish_release.py`` / ``gh``.
Gitee and GitCode are the two mirrors that do not receive the GitHub asset
automatically; this script creates their release pages and attaches the same
installer files.  Credentials live in ``~/.ww_repo_creds.json`` (0600).

Usage:
    python scripts/publish_mirrors.py --tag v1.18.0 --asset dist/*.whl
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS = os.path.expanduser('~/.ww_repo_creds.json')
PLATFORMS = {
    'gitee': 'https://gitee.com/api/v5/repos',
    'gitcode': 'https://gitcode.com/api/v5/repos',
}


def _creds() -> dict:
    with open(CREDS, encoding='utf-8') as fh:
        return json.load(fh)


def _body(tag: str, metrics: dict) -> str:
    return (
        'World Walker %s — 规则为证。\n\n'
        'AI 负责叙述，引擎负责判定、价格、背包与存档。\n'
        '完整源码、更新日志与安装说明见仓库根目录；'
        'Windows / Linux 安装包见本 Release 附件。\n\n'
        '- %s 个 MCP 工具\n'
        '- %s 个确定性规则函数\n'
        '- %s 个可执行自检\n'
        '- 版本 %s\n'
    ) % (tag, metrics.get('tools', 74), metrics.get('rule_functions', 221),
         metrics.get('verify_scripts', 24), metrics.get('version', ''))


def _call(url: str, method='GET', payload=None, headers=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    hdrs = {'Accept': 'application/json', 'User-Agent': 'world-walker-release'}
    hdrs.update(headers or {})
    if data is not None:
        hdrs['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode('utf-8')
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', 'replace')
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = {'message': raw[:240]}
        return exc.code, parsed


def _release(platform: str, cfg: dict, tag: str, metrics: dict):
    base = PLATFORMS[platform]
    token = cfg['token']
    repo = cfg['repo']
    path = '%s/%s/releases/tags/%s' % (base, repo, tag)
    status, found = _call(path + '?access_token=' + urllib.parse.quote(token))
    if status == 200 and isinstance(found, dict):
        return found, False
    status, created = _call('%s/%s/releases?access_token=%s'
                            % (base, repo, urllib.parse.quote(token)),
                            method='POST', payload={
                                'tag_name': tag,
                                'target_commitish': 'main',
                                'name': 'World Walker ' + tag,
                                'body': _body(tag, metrics),
                                'prerelease': False,
                            })
    if status not in (200, 201) or not isinstance(created, dict):
        raise SystemExit('%s release create failed: %s %s' % (platform, status, created))
    return created, True


def _multipart(path: str) -> tuple[bytes, str]:
    boundary = '----ww-' + uuid.uuid4().hex
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    with open(path, 'rb') as fh:
        data = fh.read()
    body = (
        ('--%s\r\nContent-Disposition: form-data; name="file"; filename="%s"\r\n'
         'Content-Type: %s\r\n\r\n' % (boundary, name, ctype)).encode('utf-8')
        + data + ('\r\n--%s--\r\n' % boundary).encode('utf-8')
    )
    return body, 'multipart/form-data; boundary=%s' % boundary


def _upload(platform: str, cfg: dict, release: dict, asset: str) -> bool:
    base = PLATFORMS[platform]
    token = cfg['token']
    repo = cfg['repo']
    rid = release.get('id')
    if platform == 'gitcode':
        # GitCode's release object omits the numeric id.  Its attach endpoint
        # accepts the tag in practice on some deployments, so try both forms.
        rid = release.get('id') or release.get('tag_name')
    if not rid:
        print('  %s: release has no id/tag; skip %s' % (platform, asset))
        return False
    body, ctype = _multipart(asset)
    url = ('%s/%s/releases/%s/attach_files?access_token=%s'
           % (base, repo, urllib.parse.quote(str(rid)), urllib.parse.quote(token)))
    req = urllib.request.Request(url, data=body, method='POST',
                                 headers={'Content-Type': ctype,
                                          'User-Agent': 'world-walker-release'})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read().decode('utf-8')
            print('  %s: attached %s (%s)' % (platform, os.path.basename(asset), resp.status))
            return True
    except urllib.error.HTTPError as exc:
        print('  %s: attach failed %s %s' % (platform, exc.code, exc.read().decode('utf-8', 'replace')[:200]))
        return False
    except Exception as exc:  # noqa: BLE001
        print('  %s: attach network failure %s' % (platform, exc))
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--asset', action='append', default=[])
    parser.add_argument('--platform', action='append', choices=sorted(PLATFORMS), default=[])
    args = parser.parse_args()
    if not args.asset:
        raise SystemExit('at least one --asset is required')
    assets = [os.path.abspath(p) for p in args.asset]
    for asset in assets:
        if not os.path.isfile(asset):
            raise SystemExit('asset missing: %s' % asset)
    metrics = json.load(open(os.path.join(ROOT, 'docs', 'metrics.json'), encoding='utf-8'))
    creds = _creds()
    targets = args.platform or sorted(PLATFORMS)
    ok = True
    for platform in targets:
        cfg = creds.get(platform) or {}
        if not cfg.get('token') or not cfg.get('repo'):
            print('%s: credentials missing' % platform)
            ok = False
            continue
        print('== %s / %s ==' % (platform, cfg['repo']))
        try:
            release, created = _release(platform, cfg, args.tag, metrics)
        except SystemExit as exc:
            print(str(exc))
            ok = False
            continue
        print('  %s %s' % ('created' if created else 'found', release.get('name') or args.tag))
        for asset in assets:
            if not _upload(platform, cfg, release, asset):
                ok = False
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
