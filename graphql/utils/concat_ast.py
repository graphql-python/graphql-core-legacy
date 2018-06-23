import itertools

from ..language.ast import Document

if False:
    from typing import Iterable


def concat_ast(asts):
    # type: (Iterable[Document]) -> Document
    return Document(
        definitions=list(
            itertools.chain.from_iterable(document.definitions for document in asts)
        )
    )
