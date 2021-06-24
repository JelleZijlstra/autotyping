import argparse
from dataclasses import dataclass, field
import difflib
from typing import List, Optional
import libcst
from pathlib import Path


@dataclass
class AutoTypeTransformer(libcst.CSTTransformer):
    seen_return_statement: List[bool] = field(default_factory=lambda: [False])
    seen_raise_statement: List[bool] = field(default_factory=lambda: [False])
    seen_yield: List[bool] = field(default_factory=lambda: [False])

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> Optional[bool]:
        self.seen_return_statement.append(False)
        self.seen_raise_statement.append(False)
        self.seen_yield.append(False)

    def visit_Return(self, node: libcst.Return) -> Optional[bool]:
        self.seen_return_statement[-1] = True

    def visit_Raise(self, node: libcst.Raise) -> Optional[bool]:
        self.seen_raise_statement[-1] = True

    def visit_Yield(self, node: libcst.Yield) -> Optional[bool]:
        self.seen_yield[-1] = True

    def leave_FunctionDef(
        self, original_node: libcst.FunctionDef, updated_node: libcst.FunctionDef
    ) -> libcst.CSTNode:
        seen_return = self.seen_return_statement.pop()
        seen_raise = self.seen_raise_statement.pop()
        seen_yield = self.seen_yield.pop()
        if (
            original_node.returns is None
            and not seen_raise
            and not seen_return
            and not seen_yield
        ):
            updated_node = updated_node.with_changes(
                returns=libcst.Annotation(annotation=libcst.Name(value="None"))
            )
        return updated_node

    def leave_Param(
        self, original_node: libcst.Param, updated_node: libcst.Param
    ) -> libcst.CSTNode:
        if (
            original_node.annotation is None
            and original_node.default is not None
            and isinstance(original_node.default, libcst.Name)
            and original_node.default.value in ("True", "False")
        ):
            updated_node = updated_node.with_changes(
                annotation=libcst.Annotation(annotation=libcst.Name(value="bool"))
            )
        return updated_node


def autotype(path: Path) -> None:
    code = path.read_text()
    tree = libcst.parse_module(code)
    transformer = AutoTypeTransformer()
    new_tree = tree.visit(transformer)

    print(
        "".join(difflib.unified_diff(code.splitlines(1), new_tree.code.splitlines(1)))
    )
    path.write_text(new_tree.code)


def main() -> None:
    parser = argparse.ArgumentParser("autotyper")
    parser.add_argument("filename")
    args = parser.parse_args()
    autotype(Path(args.filename))


if __name__ == "__main__":
    main()
