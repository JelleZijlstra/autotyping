import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

import libcst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


@dataclass
class AnnotateOptional:
    name: str
    module: str
    type_name: str

    @classmethod
    def make(cls, input: str) -> "AnnotateOptional":
        name, type_path = input.split(":")
        module, type_name = type_path.rsplit(".", maxsplit=1)
        return AnnotateOptional(name, module, type_name)


@dataclass
class State:
    annotate_optionals: List[AnnotateOptional]
    auto_none: bool
    auto_boolean_arg: bool
    seen_return_statement: List[bool] = field(default_factory=lambda: [False])
    seen_raise_statement: List[bool] = field(default_factory=lambda: [False])
    seen_yield: List[bool] = field(default_factory=lambda: [False])


class AutotypeCommand(VisitorBasedCodemodCommand):

    # Add a description so that future codemodders can see what this does.
    DESCRIPTION: str = "Automatically adds simple type annotations."

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--annotate-optional",
            nargs="*",
            help="foo:bar.Baz annotates any argument named 'foo' with a default of None as 'bar.Baz'",
        )
        arg_parser.add_argument(
            "--auto-none",
            action="store_true",
            default=False,
            help="Automatically add None return types",
        )
        arg_parser.add_argument(
            "--auto-boolean-arg",
            action="store_true",
            default=False,
            help="Automatically add bool annotation to parameters with a default of True or False",
        )

    def __init__(
        self,
        context: CodemodContext,
        annotate_optional: Sequence[str],
        auto_none: bool,
        auto_boolean_arg: bool,
    ) -> None:
        super().__init__(context)
        self.state = State(
            annotate_optionals=[AnnotateOptional.make(s) for s in annotate_optional],
            auto_none=auto_none,
            auto_boolean_arg=auto_boolean_arg,
        )
        print(self.state)

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
            self.state.auto_none
            and original_node.returns is None
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
            self.state.auto_boolean_arg
            and original_node.default is not None
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
        if default_is_none:
            for anno_optional in self.state.annotate_optionals:
                if original_node.name.value == anno_optional.name:
                    AddImportsVisitor.add_needed_import(
                        self.context, anno_optional.module, anno_optional.type_name
                    )
                    AddImportsVisitor.add_needed_import(
                        self.context, "typing", "Optional"
                    )
                    type_name = libcst.Name(value=anno_optional.type_name)
                    anno = libcst.Subscript(
                        value=libcst.Name(value="Optional"),
                        slice=[
                            libcst.SubscriptElement(slice=libcst.Index(value=type_name))
                        ],
                    )
                    return updated_node.with_changes(
                        annotation=libcst.Annotation(annotation=anno)
                    )
        return updated_node
