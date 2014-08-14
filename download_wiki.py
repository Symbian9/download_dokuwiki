#!/usr/bin/env python3

import argparse
import cgi
import os
import re
import subprocess
import time

try:
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from urlparse import urlparse


def download(args):
    cmd = ['wget', '--mirror', '-p', '--html-extension', '--convert-links']
    if args.cookie is not None:
        cmd.extend(['--header', 'Cookie: %s' % args.cookie])
    cmd.append(args.homepage)
    subprocess.check_call(cmd, cwd=args.output_dir)


def modify(fn, content, args):
    content = re.sub(
        r'(?s)<div id="dokuwiki__usertools">.*?</div>', '', content)
    content = re.sub(
        r'(?s)<!-- BREADCRUMBS -->.*?</div>\s*</div>', '', content)
    content = re.sub(
        r'(?s)<form(?:\s+[a-zA-Z0-9-]+="[^"]*")*\s+class="search".*?</form>',
        '', content)

    output_dir = args.output_dir
    if not output_dir.endswith('/'):
        output_dir += '/'
    assert fn.startswith(output_dir)
    assert '\\' not in fn
    url = 'https://' + fn[len(output_dir):]
    if url.endswith('/index.html'):
        url = url[:-len('/index.html')]
    url = re.sub(r'&do=[^&]*', '', url)
    url = re.sub(r'&sectok=[^&]*', '', url)

    WARNING_HEADER_TEMPLATE = '''
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
%s
</div>
<!--OFFLINE-WARNING-END-->
    '''
    if args.offline_warning_html == 'none':
        warning_header = ''
    else:
        warning_msg_html = args.offline_warning_html % {
            'url': cgi.escape(url),
            'date': time.strftime('%Y-%m-%d'),
        }
        warning_header = WARNING_HEADER_TEMPLATE % warning_msg_html

    HEADER_START = '<div id="dokuwiki__site">'
    content = re.sub(
        re.escape(HEADER_START) + r'(?:.*?<!--OFFLINE-WARNING-END-->)?',
        HEADER_START + warning_header,
        content,
        flags=re.S)
    return content


def main():
    parser = argparse.ArgumentParser('Download dokuwiki')
    parser.add_argument(
        '--skip-download',
        action='store_false', dest='do_download', default=True)
    parser.add_argument(
        '--download-only',
        action='store_true', dest='download_only', default=False)
    parser.add_argument(
        '--homepage', metavar='URL',
        default='https://wikicn.cs.uni-duesseldorf.de/doku.php')
    parser.add_argument(
        '--output-dir', metavar='DIRECTORY',
        default='./output')
    parser.add_argument(
        '--cookie', metavar='COOKIE',
        help='Cookie to send with all requests (login token, starts with DokuWiki:)')
    parser.add_argument(
        '--offline-warning', metavar='HTML', dest='offline_warning_html',
        help='Warning to show on top of each page',
        default='This is an offline copy of <a href="%(url)s">%(url)s</a>, generated on %(date)s.')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    if args.do_download:
        download(args)

    if args.download_only:
        return

    for dirpath, dirnames, filenames in os.walk(args.output_dir):
        for basen in filenames:
            fn = os.path.join(dirpath, basen)
            assert '/.git/' not in fn
            with open(fn, 'r+b') as f:
                content = f.read()
                if not (
                        content.startswith(b'<?xml') or
                        content.startswith(b'<!DOCTYPE html')):
                    continue

                str_content = content.decode('utf-8')
                new_str_content = modify(fn, str_content, args)
                if new_str_content is not None:
                    f.seek(0)
                    f.truncate(0)
                    f.write(new_str_content.encode('utf-8'))

    root_dir = urlparse(args.homepage).netloc
    assert os.path.isdir(os.path.join(args.output_dir, root_dir))
    export_fn = root_dir + '-' + time.strftime('%Y-%m-%d') + '.tar.xz'
    subprocess.check_call(
        ['tar', '-C', args.output_dir, '-c', '--xz', '-f', export_fn,
         root_dir])
    print('Exported to %s' % export_fn)


if __name__ == '__main__':
    main()
