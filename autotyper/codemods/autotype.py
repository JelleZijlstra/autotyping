import argparse
from dataclasses import dataclass, field
from typing import List, Optional

import libcst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


@dataclass
class State:
    seen_return_statement: List[bool] = field(default_factory=lambda: [False])
    seen_raise_statement: List[bool] = field(default_factory=lambda: [False])
    seen_yield: List[bool] = field(default_factory=lambda: [False])


class AutotypeCommand(VisitorBasedCodemodCommand):

    # Add a description so that future codemodders can see what this does.
    DESCRIPTION: str = "Automatically adds simple type annotations."

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        pass

    def __init__(self, context: CodemodContext) -> None:
        super().__init__(context)
        self.state = State()

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> Optional[bool]:
        self.state.seen_return_statement.append(False)
        self.state.seen_raise_statement.append(False)
        self.state.seen_yield.append(False)

    def visit_Return(self, node: libcst.Return) -> Optional[bool]:
        self.state.seen_return_statement[-1] = True

    def visit_Raise(self, node: libcst.Raise) -> Optional[bool]:
        self.state.seen_raise_statement[-1] = True

    def visit_Yield(self, node: libcst.Yield) -> Optional[bool]:
        self.state.seen_yield[-1] = True

    def leave_FunctionDef(
        self, original_node: libcst.FunctionDef, updated_node: libcst.FunctionDef
    ) -> libcst.CSTNode:
        seen_return = self.state.seen_return_statement.pop()
        seen_raise = self.state.seen_raise_statement.pop()
        seen_yield = self.state.seen_yield.pop()
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
        if original_node.annotation is not None:
            return updated_node
        if (
            original_node.default is not None
            and isinstance(original_node.default, libcst.Name)
            and original_node.default.value in ("True", "False")
        ):
            return updated_node.with_changes(
                annotation=libcst.Annotation(annotation=libcst.Name(value="bool"))
            )
        default_is_none = (
            original_node.default is not None
            and isinstance(original_node.default, libcst.Name)
            and original_node.default.value == "None"
        )
        if default_is_none and original_node.name == "uid":
            AddImportsVisitor.add_needed_import(self.context, "qtype", "Uid")
            return updated_node.with_changes(
                annotation=libcst.Annotation(annotation=libcst.Name(value="Uid"))
            )
        return updated_node
