#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画像に埋め込まれた font をチェックするスクリプト
"""
from __future__ import unicode_literals, print_function
import os
import re
import tempfile
import subprocess
import glob
import logging

import click


_log = logging.getLogger(__name__)


LATEX_TEMPLATE_START = r"""
\documentclass[a4paper]{{jarticle}}
\usepackage{{graphicx}}

\begin{{document}}
"""

LATEX_TEMPLATE_FIGURE = r"""
\begin{{figure}}
    \includegraphics{{{0}}}
\end{{figure}}
"""

LATEX_TEMPLATE_END = r"""
\end{{document}}
"""

output_pattern = re.compile(r"[\r\n]+")
pdffonts_parse_pattern = re.compile(r"""
(?P<name>.+)  # フォント名
\s+
(?P<type>type .+)  # フォントタイプ
\s{2,}
(?P<emb>\w+)\s+(?P<sub>\w+)\s+(?P<uni>\w+)  # フラグ関係
\s+
(?P<object_id>\d+\s+\d+)  # object id
""", re.VERBOSE | re.IGNORECASE)


def convert_ext(base_name, ext):
    """
    拡張子を変更する関数

    Parameters
    ----------
    base_name : str
        元のファイル名

    ext : str
        新しく設定した拡張子

    Returns
    -------
    file_name : str
        新しい拡張子に設定されたファイル名
    """
    base = os.path.splitext(base_name)[0]
    return base + "." + ext


def to_str(text):
    encoding = ["sjis", "utf8"]
    for enc in encoding:
        try:
            return text.decode(enc)
        except (UnicodeDecodeError):
            pass


def make_image_pdf(image_files):
    """
    画像単独のpdfファイルを作成する関数

    Parameters
    -----------
    image_files : list of str
        画像のパス

    Returns
    -------
    pdf_file : str
        作成したpdfファイル名
    """
    tmp_dir = tempfile.mkdtemp()
    _log.debug(tmp_dir)
    try:
        # temp ファイルをオープン
        fd, file_name = tempfile.mkstemp(suffix=".txt", dir=tmp_dir)
        # 擬似pdfを作成
        with open(file_name, "w") as f:
            f.write(LATEX_TEMPLATE_START)
            for image_file in image_files:
                _log.debug(image_file)
                image_file = os.path.abspath(image_file)
                image_file = image_file.replace("\\", "/")
                f.write(LATEX_TEMPLATE_FIGURE.format(image_file))
            f.write(LATEX_TEMPLATE_END)
        # 作業ディレクトリへ移動
        cwd = os.getcwd()
        os.chdir(tmp_dir)
        cmd = ["platex", file_name]
        if subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            dvi_file = convert_ext(file_name, "dvi")
            cmd = ["dvipdfmx", dvi_file]
            subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # pdf_file
        pdf_file = convert_ext(file_name, "pdf")
        if os.path.exists(pdf_file):
            return pdf_file
        else:
            raise RuntimeError("Failed to create pdf files")
    finally:
        os.close(fd)
        os.chdir(cwd)


def check_font_type(image_files):
    """
    画像単独のpdfファイルを作成する関数

    Parameters
    -----------
    image_files : list of str
        画像のパス

    Returns
    -------
    include_fonts : list of str
        pdfに含まれるfont typeのリスト
    """
    pdf_file = make_image_pdf(image_files)
    # pdffonts を使ってfontを探す
    cmd = ["pdffonts", pdf_file]
    output = subprocess.check_output(cmd)
    output = to_str(output)
    output = output_pattern.split(output)
    # 出力の処理
    parse_results = [pdffonts_parse_pattern.match(out) for out in output]
    include_fonts = [result.group("type") for result in parse_results if result is not None]

    return include_fonts


@click.command()
@click.argument("image_files", nargs=-1)
@click.option("--type", type=str, help="フィルターするフォントタイプを指定する")
@click.option("--ignorecase", "-i", is_flag=True)
@click.option("--log_level", "-l", default="INFO")
def main(image_files, type, ignorecase, log_level):
    _log.setLevel(getattr(logging, log_level.upper()))
    _log.addHandler(logging.StreamHandler())
    # wildcard 展開
    image_files = list(image_files)
    for f in image_files:
        if "*" in f or "?" in f:
            image_files.remove(f)
            image_files.extend(glob.glob(f))

    # フラグチェック
    if type:
        flag = 0
        if ignorecase:
            flag = re.IGNORECASE
        font_pattern = re.compile(r"{type}".format(**locals()), flag)

    font_types = check_font_type(image_files)
    for font_type in font_types:
        if type:
            r = font_pattern.match(font_type)
            if r:
                print("{f}: {font_type}".format(*locals()))
        else:
            print("{f}: {font_type}".format(**locals()))

if __name__ == "__main__":
    main()