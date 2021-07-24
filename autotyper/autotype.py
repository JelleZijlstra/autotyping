import argparse
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Set, Type

import libcst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.codemod.visitors import AddImportsVisitor


@dataclass
class NamedParam:
    name: str
    module: str
    type_name: str

    @classmethod
    def make(cls, input: str) -> "NamedParam":
        name, type_path = input.split(":")
        module, type_name = type_path.rsplit(".", maxsplit=1)
        return NamedParam(name, module, type_name)


@dataclass
class State:
    annotate_optionals: List[NamedParam]
    annotate_named_params: List[NamedParam]
    annotate_magics: bool
    annotate_imprecise_magics: bool
    none_return: bool
    scalar_return: bool
    param_types: Set[Type[object]]
    seen_return_statement: List[bool] = field(default_factory=lambda: [False])
    seen_return_types: List[Set[Type[object]]] = field(default_factory=lambda: [set()])
    seen_raise_statement: List[bool] = field(default_factory=lambda: [False])
    seen_yield: List[bool] = field(default_factory=lambda: [False])
    in_lambda: bool = False


SIMPLE_MAGICS = {
    "__str__": "str",
    "__repr__": "str",
    "__len__": "int",
    "__init__": "None",
    "__del__": "None",
    "__bool__": "bool",
    "__bytes__": "bytes",
    "__format__": "str",
    "__contains__": "bool",
    "__complex__": "complex",
    "__int__": "int",
    "__float__": "float",
    "__index__": "int",
}
IMPRECISE_MAGICS = {
    "__iter__": ("typing", "Iterator"),
    "__reversed__": ("typing", "Iterator"),
    "__await__": ("typing", "Iterator"),
}


class AutotypeCommand(VisitorBasedCodemodCommand):

    # Add a description so that future codemodders can see what this does.
    DESCRIPTION: str = "Automatically adds simple type annotations."

    @staticmethod
    def add_args(arg_parser: argparse.ArgumentParser) -> None:
        arg_parser.add_argument(
            "--annotate-optional",
            nargs="*",
            help=(
                "foo:bar.Baz annotates any argument named 'foo' with a default of None"
                " as 'bar.Baz'"
            ),
        )
        arg_parser.add_argument(
            "--annotate-named-param",
            nargs="*",
            help=(
                "foo:bar.Baz annotates any argument named 'foo' with no default"
                " as 'bar.Baz'"
            ),
        )
        arg_parser.add_argument(
            "--none-return",
            action="store_true",
            default=False,
            help="Automatically add None return types",
        )
        arg_parser.add_argument(
            "--scalar-return",
            action="store_true",
            default=False,
            help="Automatically add int, str, bytes, float, and bool return types",
        )
        arg_parser.add_argument(
            "--bool-param",
            action="store_true",
            default=False,
            help=(
                "Automatically add bool annotation to parameters with a default of True"
                " or False"
            ),
        )
        arg_parser.add_argument(
            "--int-param",
            action="store_true",
            default=False,
            help=("Automatically add int annotation to parameters with an int default"),
        )
        arg_parser.add_argument(
            "--float-param",
            action="store_true",
            default=False,
            help=(
                "Automatically add float annotation to parameters with a float default"
            ),
        )
        arg_parser.add_argument(
            "--str-param",
            action="store_true",
            default=False,
            help=("Automatically add str annotation to parameters with a str default"),
        )
        arg_parser.add_argument(
            "--bytes-param",
            action="store_true",
            default=False,
            help=(
                "Automatically add bytes annotation to parameters with a bytes default"
            ),
        )
        arg_parser.add_argument(
            "--annotate-magics",
            action="store_true",
            default=False,
            help="Add annotations to certain magic methods (e.g., __str__)",
        )
        arg_parser.add_argument(
            "--annotate-imprecise-magics",
            action="store_true",
            default=False,
            help=(
                "Add annotations to magic methods that are less precise (e.g., Iterable "
                "for __iter__)"
            ),
        )

    def __init__(
        self,
        context: CodemodContext,
        *,
        annotate_optional: Optional[Sequence[str]] = None,
        annotate_named_param: Optional[Sequence[str]] = None,
        annotate_magics: bool = False,
        annotate_imprecise_magics: bool = False,
        none_return: bool = False,
        scalar_return: bool = False,
        bool_param: bool = False,
        str_param: bool = False,
        bytes_param: bool = False,
        float_param: bool = False,
        int_param: bool = False,
    ) -> None:
        super().__init__(context)
        param_type_pairs = [
            (bool_param, bool),
            (str_param, str),
            (bytes_param, bytes),
            (int_param, int),
            (float_param, float),
        ]
        self.state = State(
            annotate_optionals=[NamedParam.make(s) for s in annotate_optional]
            if annotate_optional
            else [],
            annotate_named_params=[NamedParam.make(s) for s in annotate_named_param]
            if annotate_named_param
            else [],
            none_return=none_return,
            scalar_return=scalar_return,
            param_types={typ for param, typ in param_type_pairs if param},
            annotate_magics=annotate_magics,
            annotate_imprecise_magics=annotate_imprecise_magics,
        )

    def visit_FunctionDef(self, node: libcst.FunctionDef) -> Optional[bool]:
        self.state.seen_return_statement.append(False)
        self.state.seen_raise_statement.append(False)
        self.state.seen_yield.append(False)
        self.state.seen_return_types.append(set())

    def visit_Return(self, node: libcst.Return) -> Optional[bool]:
        if node.value is not None:
            self.state.seen_return_statement[-1] = True
            self.state.seen_return_types[-1].add(type_of_expression(node.value))
        else:
            self.state.seen_return_types[-1].add(None)

    def visit_Raise(self, node: libcst.Raise) -> Optional[bool]:
        self.state.seen_raise_statement[-1] = True

    def visit_Yield(self, node: libcst.Yield) -> Optional[bool]:
        self.state.seen_yield[-1] = True

    def visit_Lambda(self, node: libcst.Lambda) -> Optional[bool]:
        self.state.in_lambda = True

    def leave_Lambda(
        self, original_node: libcst.Lambda, updated_node: libcst.Lambda
    ) -> libcst.CSTNode:
        self.state.in_lambda = False
        return updated_node

    def leave_FunctionDef(
        self, original_node: libcst.FunctionDef, updated_node: libcst.FunctionDef
    ) -> libcst.CSTNode:
        seen_return = self.state.seen_return_statement.pop()
        seen_raise = self.state.seen_raise_statement.pop()
        seen_yield = self.state.seen_yield.pop()
        return_types = self.state.seen_return_types.pop()
        name = original_node.name.value
        if self.state.annotate_magics and name in ("__exit__", "__aexit__"):
            updated_node = self.annotate_exit(updated_node)

        if original_node.returns is not None:
            return updated_node

        if self.state.annotate_magics:
            if name in SIMPLE_MAGICS:
                return updated_node.with_changes(
                    returns=libcst.Annotation(
                        annotation=libcst.Name(value=SIMPLE_MAGICS[name])
                    )
                )
        if self.state.annotate_imprecise_magics:
            if name in IMPRECISE_MAGICS:
                module, imported_name = IMPRECISE_MAGICS[name]
                AddImportsVisitor.add_needed_import(self.context, module, imported_name)
                return updated_node.with_changes(
                    returns=libcst.Annotation(
                        annotation=libcst.Name(value=imported_name)
                    )
                )

        if (
            self.state.none_return
            and not seen_raise
            and not seen_return
            and not seen_yield
        ):
            return updated_node.with_changes(
                returns=libcst.Annotation(annotation=libcst.Name(value="None"))
            )

        if self.state.scalar_return and not seen_yield and len(return_types) == 1:
            return_type = next(iter(return_types))
            if return_type in {bool, int, float, str, bytes}:
                return updated_node.with_changes(
                    returns=libcst.Annotation(
                        annotation=libcst.Name(value=return_type.__name__)
                    )
                )

        return updated_node

    def annotate_exit(self, node: libcst.FunctionDef) -> libcst.FunctionDef:
        if (
            node.params.star_arg is not libcst.MaybeSentinel.DEFAULT
            or node.params.kwonly_params
            or node.params.star_kwarg
        ):
            return node
        # 4 for def __exit__(self, type, value, tb)
        if len(node.params.params) == 4:
            params = node.params.params
            is_pos_only = False
        elif len(node.params.posonly_params) == 4:
            params = node.params.posonly_params
            is_pos_only = True
        else:
            return node
        new_params = [params[0]]

        # type
        if params[1].annotation:
            new_params.append(params[1])
        else:
            AddImportsVisitor.add_needed_import(self.context, "typing", "Optional")
            AddImportsVisitor.add_needed_import(self.context, "typing", "Type")
            type_anno = libcst.Subscript(
                value=libcst.Name(value="Type"),
                slice=[
                    libcst.SubscriptElement(
                        slice=libcst.Index(value=libcst.Name(value="BaseException"))
                    )
                ],
            )
            anno = libcst.Subscript(
                value=libcst.Name(value="Optional"),
                slice=[libcst.SubscriptElement(slice=libcst.Index(value=type_anno))],
            )
            new_params.append(
                params[1].with_changes(annotation=libcst.Annotation(annotation=anno))
            )

        # value
        if params[2].annotation:
            new_params.append(params[2])
        else:
            AddImportsVisitor.add_needed_import(self.context, "typing", "Optional")
            anno = libcst.Subscript(
                value=libcst.Name(value="Optional"),
                slice=[
                    libcst.SubscriptElement(
                        slice=libcst.Index(value=libcst.Name(value="BaseException"))
                    )
                ],
            )
            new_params.append(
                params[2].with_changes(annotation=libcst.Annotation(annotation=anno))
            )

        # tb
        if params[3].annotation:
            new_params.append(params[3])
        else:
            AddImportsVisitor.add_needed_import(self.context, "types", "TracebackType")
            anno = libcst.Subscript(
                value=libcst.Name(value="Optional"),
                slice=[
                    libcst.SubscriptElement(
                        slice=libcst.Index(value=libcst.Name(value="TracebackType"))
                    )
                ],
            )
            new_params.append(
                params[3].with_changes(annotation=libcst.Annotation(annotation=anno))
            )

        if is_pos_only:
            new_parameters = node.params.with_changes(posonly_params=new_params)
        else:
            new_parameters = node.params.with_changes(params=new_params)
        return node.with_changes(params=new_parameters)

    def leave_Param(
        self, original_node: libcst.Param, updated_node: libcst.Param
    ) -> libcst.CSTNode:
        if self.state.in_lambda:
            # Lambdas can't have annotations
            return updated_node
        if original_node.annotation is not None:
            return updated_node
        if original_node.default is not None:
            default_type = type_of_expression(original_node.default)
            if default_type in self.state.param_types:
                return updated_node.with_changes(
                    annotation=libcst.Annotation(
                        annotation=libcst.Name(value=default_type.__name__)
                    )
                )

        default_is_none = (
            original_node.default is not None
            and isinstance(original_node.default, libcst.Name)
            and original_node.default.value == "None"
        )
        if default_is_none:
            for anno_optional in self.state.annotate_optionals:
                if original_node.name.value == anno_optional.name:
                    return self._annotate_param(
                        anno_optional, updated_node, optional=True
                    )
        elif original_node.default is None:
            for anno_named_param in self.state.annotate_named_params:
                if original_node.name.value == anno_named_param.name:
                    return self._annotate_param(anno_named_param, updated_node)
        return updated_node

    def _annotate_param(
        self, param: NamedParam, updated_node: libcst.Param, optional: bool = False
    ) -> None:
        AddImportsVisitor.add_needed_import(self.context, param.module, param.type_name)
        if optional:
            AddImportsVisitor.add_needed_import(self.context, "typing", "Optional")
        type_name = libcst.Name(value=param.type_name)
        if optional:
            anno = libcst.Subscript(
                value=libcst.Name(value="Optional"),
                slice=[libcst.SubscriptElement(slice=libcst.Index(value=type_name))],
            )
        else:
            anno = type_name
        return updated_node.with_changes(annotation=libcst.Annotation(annotation=anno))


def type_of_expression(expr: libcst.BaseExpression) -> Optional[Type[object]]:
    """Very simple type inference for expressions.

    Return None if the type cannot be inferred.

    """
    if isinstance(expr, libcst.Float):
        return float
    elif isinstance(expr, libcst.Integer):
        return int
    elif isinstance(expr, libcst.Imaginary):
        return complex
    elif isinstance(expr, libcst.FormattedString):
        return str  # f-strings can only be str, not bytes
    elif isinstance(expr, libcst.SimpleString):
        if "b" in expr.prefix:
            return bytes
        else:
            return str
    elif isinstance(expr, libcst.ConcatenatedString):
        left = type_of_expression(expr.left)
        right = type_of_expression(expr.right)
        if left == right:
            return left
        else:
            return None
    elif isinstance(expr, libcst.Name) and expr.value in ("True", "False"):
        return bool
    else:
        return None
