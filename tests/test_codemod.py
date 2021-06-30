from libcst.codemod import CodemodTest
from autotyper.autotype import AutotypeCommand


class TestAutotype(CodemodTest):
    TRANSFORM = AutotypeCommand

    def test_noop(self) -> None:
        before = """
            def f():
                pass
        """
        after = """
            def f():
                pass
        """

        # By default, we do nothing.
        self.assertCodemod(before, after)

    def test_none_return(self) -> None:
        before = """
            def foo():
                pass

            def bar():
                return 1

            def baz():
                return
        """
        after = """
            def foo() -> None:
                pass

            def bar():
                return 1

            def baz() -> None:
                return
        """
        self.assertCodemod(before, after, none_return=True)

    def test_bool_param(self) -> None:
        before = """
            def foo(x = False, y = 0, z: int = False):
                pass
        """
        after = """
            def foo(x: bool = False, y = 0, z: int = False):
                pass
        """
        self.assertCodemod(before, after, bool_param=True)

    def test_annotate_optional(self) -> None:
        before = """
            def foo(uid=None, qid=None):
                pass

            def bar(uid):
                pass
        """
        after = """
            from my_types import Uid
            from typing import Optional

            def foo(uid: Optional[Uid]=None, qid=None):
                pass

            def bar(uid):
                pass
        """
        self.assertCodemod(before, after, annotate_optional=["uid:my_types.Uid"])

    def test_annotate_named_param(self) -> None:
        before = """
            def foo(uid, qid):
                pass

            def bar(uid=1):
                pass
        """
        after = """
            from my_types import Uid

            def foo(uid: Uid, qid):
                pass

            def bar(uid=1):
                pass
        """
        self.assertCodemod(before, after, annotate_named_param=["uid:my_types.Uid"])

    def test_annotate_magics(self) -> None:
        before = """
            def __str__():
                pass

            def __not_str__():
                pass
        """
        after = """
            def __str__() -> str:
                pass

            def __not_str__():
                pass
        """
        self.assertCodemod(before, after, annotate_magics=True)

    def test_annotate_imprecise_magics(self) -> None:
        before = """
            def __iter__():
                pass

            def __not_iter__():
                pass
        """
        after = """
            from typing import Iterator

            def __iter__() -> Iterator:
                pass

            def __not_iter__():
                pass
        """
        self.assertCodemod(before, after, annotate_imprecise_magics=True)
