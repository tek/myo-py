#!usr/bin/env python3

from amino import Path, List, Nil

from ribosome.util.doc.write import write_default_docs
from ribosome.util.doc.data import StaticDoc, DocBlock, DocLine, DocString, Headline, NoMeta, GeneralAnchor, Anchor
from myo.config import settings

pkg_dir = Path(__file__).absolute().parent.parent
intro: DocBlock[None] = DocBlock(List(
    DocLine(DocString('Introduction', Headline.cons(1, Anchor('myo', GeneralAnchor())))),
), NoMeta())
pre = List(intro)
post = Nil
static = StaticDoc(pre, post)
write_default_docs('myo.components', List(settings), pkg_dir, 'myo', 'myo', static)
