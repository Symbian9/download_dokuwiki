#!/usr/bin/env python3

import argparse
import cgi
import os
import re
import subprocess
import time


def download(args):
    cmd = ['wget', '--mirror', '-p', '--html-extension', '--convert-links']
    if args.cookie is not None:
        cmd.extend(['--header', 'Cookie: %s' % args.cookie])
    cmd.append(args.homepage)
    subprocess.check_call(cmd)


def modify(fn, content):
    content = re.sub(
        r'(?s)<div id="dokuwiki__usertools">.*?</div>', '', content)
    content = re.sub(
        r'(?s)<!-- BREADCRUMBS -->.*?</div>\s*</div>', '', content)
    content = re.sub(
        r'(?s)<form(?:\s+[a-zA-Z0-9-]+="[^"]*")*\s+class="search".*?</form>',
        '', content)

    assert fn.startswith('./')
    assert '\\' not in fn
    url = 'https://' + fn[len('./'):]
    if url.endswith('/index.html'):
        url = url[:-len('/index.html')]
    url = re.sub(r'&do=[^&]*', '', url)
    url = re.sub(r'&sectok=[^&]*', '', url)

    WARNING_HEADER = '''
<style>
.offline_warning {
    font-size: 16px;
    text-align: center;
    padding: 10px 0; margin-bottom: -20px;
    background: red*; background: rgba(255, 0, 0, 0.5);
}
@media print {
    .offline_warning {display: none;}
}
</style>
<div class="offline_warning">
This is an offline copy of <a href="%(url)s">%(url)s</a>, generated on %(date)s.
</div>
<!--OFFLINE-WARNING-END-->
    ''' % {
        'url': cgi.escape(url),
        'date': time.strftime('%Y-%m-%d'),
    }

    HEADER_START = '<div id="dokuwiki__site">'
    content = re.sub(
        re.escape(HEADER_START) + r'(?:.*?<!--OFFLINE-WARNING-END-->)?',
        HEADER_START + WARNING_HEADER,
        content,
        flags=re.S)
    return content


def main():
    parser = argparse.ArgumentParser('Download dokuwiki')
    parser.add_argument(
        '--skip-download',
        action='store_false', dest='do_download', default=True)
    parser.add_argument(
        '--homepage', metavar='URL',
        default='https://wikicn.cs.uni-duesseldorf.de/doku.php')
    parser.add_argument('--cookie', metavar='COOKIE')
    args = parser.parse_args()

    if args.do_download:
        download(args)

    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames.remove('.git')
        for basen in filenames:
            fn = os.path.join(dirpath, basen)
            assert '.git' not in filename
            with open(fn, 'r+b') as f:
                content = f.read()
                if not (
                        content.startswith(b'<?xml') or
                        content.startswith(b'<!DOCTYPE html')):
                    continue

                str_content = content.decode('utf-8')
                new_str_content = modify(fn, str_content)
                if new_str_content is not None:
                    f.seek(0)
                    f.truncate(0)
                    f.write(new_str_content.encode('utf-8'))

if __name__ == '__main__':
    main()
